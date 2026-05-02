"""
台股加權指數與匯率服務。

加權指數來源：證交所 MI_5MINS_HIST（按月取整月資料）
匯率來源：台銀牌告匯率 fltxt（僅當日）

策略：
- 加權指數可批量補抓（按月取）
- 匯率只有當日即時資料，歷史匯率從每日排程累積
"""

from datetime import datetime, timezone, date

import httpx
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.daily_market import DAILY_MARKET_COLLECTION
from app.models.taiex_exchange import TAIEX_EXCHANGE_COLLECTION
from app.utils.time import now_log_prefix

# 證交所加權指數月資料 API
TWSE_TAIEX_API = "https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST"
# 台銀牌告匯率
BOT_RATE_API = "https://rate.bot.com.tw/xrt/fltxt/0/day"


def _roc_to_date(roc_str: str) -> str:
    """民國年日期轉西元，例如 '115/04/30' → '2026-04-30'"""
    parts = roc_str.strip().split("/")
    year = int(parts[0]) + 1911
    return f"{year}-{parts[1]}-{parts[2]}"


def _parse_float(s: str) -> float:
    """解析數字字串，移除逗號"""
    return float(s.replace(",", ""))


async def fetch_taiex_month(year: int, month: int) -> list[dict]:
    """
    從證交所取得指定月份的加權指數資料。

    Returns:
        [{"date": "2026-04-01", "open": ..., "high": ..., "low": ..., "close": ...}, ...]
    """
    date_str = f"{year}{month:02d}01"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            TWSE_TAIEX_API,
            params={"date": date_str, "response": "json"},
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("stat") != "OK" or not data.get("data"):
        return []

    # 格式: ['115/04/01', '開盤', '最高', '最低', '收盤']
    results = []
    for row in data["data"]:
        results.append({
            "date": _roc_to_date(row[0]),
            "taiex_open": _parse_float(row[1]),
            "taiex_high": _parse_float(row[2]),
            "taiex_low": _parse_float(row[3]),
            "taiex_close": _parse_float(row[4]),
        })
    return results


async def fetch_usd_twd_rate() -> dict | None:
    """
    從台銀取得當日 USD/TWD 即期匯率。

    Returns:
        {"usd_twd_buy": 31.575, "usd_twd_sell": 31.725} 或 None
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(BOT_RATE_API)
            resp.raise_for_status()
            for line in resp.text.strip().split("\n"):
                if line.startswith("USD"):
                    parts = line.split()
                    # parts: ['USD', '本行買入', 現金買, 即期買, ..., '本行賣出', 現金賣, 即期賣, ...]
                    buy_idx = parts.index("本行買入")
                    sell_idx = parts.index("本行賣出")
                    return {
                        "usd_twd_buy": float(parts[buy_idx + 2]),   # 即期買入
                        "usd_twd_sell": float(parts[sell_idx + 2]),  # 即期賣出
                    }
    except Exception as e:
        logger.warning(f"取得台銀匯率失敗: {e}")
    return None


async def _append_fetch_log(db: AsyncIOMotorDatabase, date_str: str, log_line: str) -> None:
    collection = db[DAILY_MARKET_COLLECTION]
    doc = await collection.find_one({"date": date_str})
    current_log = doc.get("fetch_log", "") if doc else ""
    separator = "\n" if current_log else ""
    new_log = f"{current_log}{separator}{log_line}"
    await collection.update_one(
        {"date": date_str},
        {"$set": {"fetch_log": new_log, "updated_at": datetime.now(timezone.utc)}},
    )


async def check_and_save_taiex_exchange(
    db: AsyncIOMotorDatabase,
    target_date: date,
) -> dict:
    """
    抓取台股指數與匯率並存入獨立資料表。

    加權指數：從證交所按月取（會快取同月其他日期）
    匯率：僅當日可取，歷史日期只存指數不存匯率
    """
    date_str = target_date.strftime("%Y-%m-%d")
    fetch_collection = db[DAILY_MARKET_COLLECTION]
    data_collection = db[TAIEX_EXCHANGE_COLLECTION]

    # 檢查是否已有資料
    existing = await data_collection.find_one({"date": date_str})
    if existing:
        logger.info(f"{date_str} 台股指數匯率已存在，跳過")
        return {"date": date_str, "status": "skipped", "detail": "已抓取過"}

    # 檢查開盤狀態
    fetch_doc = await fetch_collection.find_one({"date": date_str})
    if fetch_doc is None or fetch_doc.get("twse_is_open") is None:
        return {"date": date_str, "status": "skipped", "detail": "尚無開盤狀態"}
    if not fetch_doc.get("twse_is_open"):
        return {"date": date_str, "status": "closed", "detail": "休市日"}

    now = datetime.now(timezone.utc)
    try:
        # 取加權指數（整月取，找到目標日期）
        month_data = await fetch_taiex_month(target_date.year, target_date.month)
        taiex = next((d for d in month_data if d["date"] == date_str), None)

        if taiex is None:
            raise RuntimeError(f"{date_str} 在證交所月資料中找不到")

        # 同時把同月其他日期也存入（批量補抓）
        for item in month_data:
            item_date = item["date"]
            item_existing = await data_collection.find_one({"date": item_date})
            if not item_existing:
                await data_collection.insert_one({
                    **item,
                    "usd_twd_buy": None,
                    "usd_twd_sell": None,
                    "created_at": now,
                    "updated_at": now,
                })

        # 如果是今天，嘗試取匯率
        today = date.today()
        if target_date == today:
            rate = await fetch_usd_twd_rate()
            if rate:
                await data_collection.update_one(
                    {"date": date_str},
                    {"$set": {**rate, "updated_at": now}},
                )
                logger.info(f"{date_str} 匯率已更新: USD/TWD 買={rate['usd_twd_buy']} 賣={rate['usd_twd_sell']}")

        # 更新旗標
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"taiex_exchange": True, "updated_at": now}},
        )
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} taiex_exchange: 抓取成功")

        close_val = taiex["taiex_close"]
        logger.info(f"{date_str} 台股指數已儲存，收盤: {close_val:,.2f}")
        return {"date": date_str, "status": "fetched", "detail": f"收盤: {close_val:,.2f}"}

    except Exception as e:
        error_msg = str(e)
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"taiex_exchange": False, "updated_at": now}},
        )
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} taiex_exchange: 抓取失敗 - {error_msg}")
        logger.error(f"{date_str} 台股指數匯率抓取失敗: {error_msg}")
        raise
