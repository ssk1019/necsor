"""
台指期未平倉口數服務。

資料來源：FinMind API
dataset: TaiwanFuturesDaily, data_id: TX

回傳各合約月份的成交量、未平倉口數、收盤價等。
分為一般交易時段和盤後交易時段。

抓取的數據存入獨立資料表 futures_open_interest。
抓取狀態旗標記錄在 daily_market_fetch.futures_oi。
抓取日誌記錄在 daily_market_fetch.fetch_log。
"""

from datetime import datetime, timezone, date

import httpx
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.models.daily_market import DAILY_MARKET_COLLECTION
from app.models.futures_oi import FUTURES_OI_COLLECTION
from app.utils.time import now_log_prefix

# FinMind API
FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"


async def fetch_futures_oi_data(target_date: date) -> dict:
    """
    從 FinMind API 抓取指定日期的台指期資料。

    Args:
        target_date: 要查詢的日期

    Returns:
        結構化的台指期資料 dict

    Raises:
        RuntimeError: API 回傳異常或無資料
    """
    settings = get_settings()
    date_str = target_date.strftime("%Y-%m-%d")

    logger.info(f"正在從 FinMind 抓取 {target_date} 台指期資料...")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            FINMIND_API_URL,
            params={
                "dataset": "TaiwanFuturesDaily",
                "data_id": "TX",
                "start_date": date_str,
                "end_date": date_str,
                "token": settings.FINMIND_API_TOKEN,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != 200 or not data.get("data"):
        msg = data.get("msg", "未知錯誤")
        raise RuntimeError(f"FinMind API 回傳異常: {msg}")

    rows = data["data"]
    if not rows:
        raise RuntimeError(f"{target_date} 無台指期資料")

    # 整理各合約明細
    contracts = []
    total_volume = 0
    total_oi = 0
    front_month_close = 0.0
    front_month_oi = 0
    front_month_contract = None

    for row in rows:
        contract = {
            "contract_date": row["contract_date"],
            "open": row.get("open", 0),
            "high": row.get("max", 0),
            "low": row.get("min", 0),
            "close": row.get("close", 0),
            "volume": row.get("volume", 0),
            "open_interest": row.get("open_interest", 0),
            "settlement_price": row.get("settlement_price", 0),
            "trading_session": row.get("trading_session", ""),
        }
        contracts.append(contract)
        total_volume += contract["volume"]
        total_oi += contract["open_interest"]

        # 找近月合約（一般交易時段、最小合約月份）
        if row.get("trading_session") != "after_market":
            if front_month_contract is None or row["contract_date"] < front_month_contract:
                front_month_contract = row["contract_date"]
                front_month_close = contract["close"]
                front_month_oi = contract["open_interest"]

    logger.info(
        f"已取得 {target_date} 台指期資料，"
        f"近月收盤: {front_month_close}，總未平倉: {total_oi:,}，總成交量: {total_volume:,}"
    )

    return {
        "total_volume": total_volume,
        "total_oi": total_oi,
        "front_month_close": front_month_close,
        "front_month_oi": front_month_oi,
        "contracts": contracts,
    }


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


async def check_and_save_futures_oi(
    db: AsyncIOMotorDatabase,
    target_date: date,
) -> dict:
    """
    抓取台指期未平倉口數並存入獨立資料表。

    Returns:
        {"date": "...", "status": "fetched" | "skipped" | "closed", "detail": "..."}
    """
    date_str = target_date.strftime("%Y-%m-%d")
    fetch_collection = db[DAILY_MARKET_COLLECTION]
    data_collection = db[FUTURES_OI_COLLECTION]

    # 檢查獨立表是否已有資料
    existing = await data_collection.find_one({"date": date_str})
    if existing:
        logger.info(f"{date_str} 台指期資料已存在，跳過")
        return {"date": date_str, "status": "skipped", "detail": "已抓取過"}

    # 檢查當日是否有開盤
    fetch_doc = await fetch_collection.find_one({"date": date_str})
    if fetch_doc is None or fetch_doc.get("twse_is_open") is None:
        logger.warning(f"{date_str} 尚無開盤狀態資料，跳過台指期抓取")
        return {"date": date_str, "status": "skipped", "detail": "尚無開盤狀態"}

    if not fetch_doc.get("twse_is_open"):
        logger.info(f"{date_str} 休市，不抓取台指期資料")
        return {"date": date_str, "status": "closed", "detail": "休市日"}

    # 抓取資料
    now = datetime.now(timezone.utc)
    try:
        futures_data = await fetch_futures_oi_data(target_date)

        doc = {
            "date": date_str,
            **futures_data,
            "created_at": now,
            "updated_at": now,
        }
        await data_collection.insert_one(doc)

        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"futures_oi": True, "updated_at": now}},
        )

        await _append_fetch_log(db, date_str, f"{now_log_prefix()} futures_oi: 抓取成功")

        logger.info(f"{date_str} 台指期資料已儲存")
        return {
            "date": date_str,
            "status": "fetched",
            "detail": f"近月收盤: {futures_data['front_month_close']}，總OI: {futures_data['total_oi']:,}",
        }

    except Exception as e:
        error_msg = str(e)
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"futures_oi": False, "updated_at": now}},
        )
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} futures_oi: 抓取失敗 - {error_msg}")
        logger.error(f"{date_str} 台指期抓取失敗: {error_msg}")
        raise
