"""
融資融券餘額統計服務。

資料來源：證交所官方 API
https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN

selectType=MS 為彙總資料，回傳融資、融券、融資金額三列。

抓取的數據存入獨立資料表 margin_trading（以日期為主鍵）。
抓取狀態旗標記錄在 daily_market_fetch.margin_trading。
抓取日誌記錄在 daily_market_fetch.fetch_log。
"""

from datetime import datetime, timezone, date

import httpx
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.daily_market import DAILY_MARKET_COLLECTION
from app.models.margin_trading import MARGIN_TRADING_COLLECTION
from app.utils.time import now_log_prefix

# 證交所融資融券彙總 API
TWSE_MARGIN_API = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"


def _parse_int(s: str) -> int:
    """將逗號分隔的數字字串轉為整數"""
    return int(s.replace(",", ""))


async def fetch_margin_data(target_date: date) -> dict:
    """
    從證交所 API 抓取指定日期的融資融券彙總資料。

    Args:
        target_date: 要查詢的日期

    Returns:
        結構化的融資融券資料 dict

    Raises:
        RuntimeError: API 回傳異常或無資料
    """
    date_str = target_date.strftime("%Y%m%d")

    logger.info(f"正在從證交所抓取 {target_date} 融資融券餘額...")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            TWSE_MARGIN_API,
            params={"date": date_str, "selectType": "MS", "response": "json"},
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("stat") != "OK":
        raise RuntimeError(f"證交所 API 回傳異常: stat={data.get('stat')}")

    tables = data.get("tables", [])
    if not tables or not tables[0].get("data"):
        raise RuntimeError(f"{target_date} 無融資融券資料（可能非交易日）")

    rows = tables[0]["data"]

    # 解析資料
    # rows 格式:
    # [["融資(交易單位)", "買進", "賣出", "現金償還", "前日餘額", "今日餘額"],
    #  ["融券(交易單位)", ...],
    #  ["融資金額(仟元)", ...]]
    name_mapping = {
        "融資(交易單位)": "margin_buy",
        "融券(交易單位)": "short_sell",
        "融資金額(仟元)": "margin_buy_amount",
    }

    result = {}
    for row in rows:
        name = row[0].strip()
        key = name_mapping.get(name)
        if key is None:
            continue
        result[key] = {
            "buy": _parse_int(row[1]),
            "sell": _parse_int(row[2]),
            "cash_repay": _parse_int(row[3]),
            "prev_balance": _parse_int(row[4]),
            "today_balance": _parse_int(row[5]),
        }

    margin_bal = result.get("margin_buy", {}).get("today_balance", "N/A")
    short_bal = result.get("short_sell", {}).get("today_balance", "N/A")
    logger.info(f"已取得 {target_date} 融資融券資料，融資餘額: {margin_bal:,}，融券餘額: {short_bal:,}")
    return result


async def _append_fetch_log(db: AsyncIOMotorDatabase, date_str: str, log_line: str) -> None:
    """在 daily_market_fetch 的 fetch_log 追加一行紀錄。"""
    collection = db[DAILY_MARKET_COLLECTION]
    doc = await collection.find_one({"date": date_str})
    current_log = doc.get("fetch_log", "") if doc else ""
    separator = "\n" if current_log else ""
    new_log = f"{current_log}{separator}{log_line}"
    await collection.update_one(
        {"date": date_str},
        {"$set": {"fetch_log": new_log, "updated_at": datetime.now(timezone.utc)}},
    )


async def check_and_save_margin(
    db: AsyncIOMotorDatabase,
    target_date: date,
) -> dict:
    """
    抓取融資融券餘額並存入獨立資料表。

    前置檢查：
    1. 獨立表是否已有該日期資料 → 有則跳過
    2. daily_market_fetch 的 twse_is_open 是否為 True → 休市日不抓取

    Returns:
        {"date": "...", "status": "fetched" | "skipped" | "closed", "detail": "..."}
    """
    date_str = target_date.strftime("%Y-%m-%d")
    fetch_collection = db[DAILY_MARKET_COLLECTION]
    data_collection = db[MARGIN_TRADING_COLLECTION]

    # 檢查獨立表是否已有資料
    existing = await data_collection.find_one({"date": date_str})
    if existing:
        logger.info(f"{date_str} 融資融券資料已存在，跳過")
        return {"date": date_str, "status": "skipped", "detail": "已抓取過"}

    # 檢查當日是否有開盤
    fetch_doc = await fetch_collection.find_one({"date": date_str})
    if fetch_doc is None or fetch_doc.get("twse_is_open") is None:
        logger.warning(f"{date_str} 尚無開盤狀態資料，跳過融資融券抓取")
        return {"date": date_str, "status": "skipped", "detail": "尚無開盤狀態"}

    if not fetch_doc.get("twse_is_open"):
        logger.info(f"{date_str} 休市，不抓取融資融券資料")
        return {"date": date_str, "status": "closed", "detail": "休市日"}

    # 抓取資料
    now = datetime.now(timezone.utc)
    try:
        margin_data = await fetch_margin_data(target_date)

        # 寫入獨立資料表
        doc = {
            "date": date_str,
            **margin_data,
            "created_at": now,
            "updated_at": now,
        }
        await data_collection.insert_one(doc)

        # 更新 daily_market_fetch 旗標
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"margin_trading": True, "updated_at": now}},
        )

        # 追加 fetch_log
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} margin_trading: 抓取成功")

        margin_bal = margin_data.get("margin_buy", {}).get("today_balance", 0)
        short_bal = margin_data.get("short_sell", {}).get("today_balance", 0)
        logger.info(f"{date_str} 融資融券已儲存，融資餘額: {margin_bal:,}，融券餘額: {short_bal:,}")
        return {"date": date_str, "status": "fetched", "detail": f"融資: {margin_bal:,} / 融券: {short_bal:,}"}

    except Exception as e:
        error_msg = str(e)
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"margin_trading": False, "updated_at": now}},
        )
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} margin_trading: 抓取失敗 - {error_msg}")
        logger.error(f"{date_str} 融資融券抓取失敗: {error_msg}")
        raise
