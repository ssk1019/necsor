"""
期貨三大法人未平倉餘額服務。

資料來源：FinMind API
dataset: TaiwanFuturesInstitutionalInvestors

支援多種期貨商品：TX（臺股）、TE（電子）、TF（金融）、XIF（非金電）。
每個商品分別抓取自營商、投信、外資的未平倉餘額。
"""

from datetime import datetime, timezone, date

import httpx
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.models.daily_market import DAILY_MARKET_COLLECTION
from app.models.futures_institutional import (
    FUTURES_INSTITUTIONAL_COLLECTION,
    FUTURES_PRODUCTS,
)
from app.utils.time import now_log_prefix

FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"

# 法人名稱對應 key
INVESTOR_MAPPING = {
    "自營商": "dealer",
    "投信": "investment_trust",
    "外資": "foreign_investor",
}


def _parse_investor_row(row: dict) -> dict:
    """解析單筆法人資料為結構化 dict。"""
    long_oi = row.get("long_open_interest_balance_volume", 0)
    short_oi = row.get("short_open_interest_balance_volume", 0)
    long_oi_amt = row.get("long_open_interest_balance_amount", 0)
    short_oi_amt = row.get("short_open_interest_balance_amount", 0)

    return {
        "name": row["institutional_investors"],
        "long_deal_volume": row.get("long_deal_volume", 0),
        "short_deal_volume": row.get("short_deal_volume", 0),
        "long_deal_amount": row.get("long_deal_amount", 0),
        "short_deal_amount": row.get("short_deal_amount", 0),
        "long_oi_volume": long_oi,
        "short_oi_volume": short_oi,
        "net_oi_volume": long_oi - short_oi,
        "long_oi_amount": long_oi_amt,
        "short_oi_amount": short_oi_amt,
        "net_oi_amount": long_oi_amt - short_oi_amt,
    }


async def fetch_futures_institutional_data(target_date: date) -> dict:
    """
    從 FinMind API 抓取指定日期所有期貨商品的三大法人資料。

    Returns:
        {"TX": {"dealer": {...}, ...}, "TE": {...}, "TF": {...}, "XIF": {...}}
    """
    settings = get_settings()
    date_str = target_date.strftime("%Y-%m-%d")
    result = {}

    async with httpx.AsyncClient(timeout=15) as client:
        for futures_id, futures_name in FUTURES_PRODUCTS.items():
            logger.debug(f"抓取 {target_date} {futures_name}({futures_id}) 三大法人...")

            resp = await client.get(
                FINMIND_API_URL,
                params={
                    "dataset": "TaiwanFuturesInstitutionalInvestors",
                    "data_id": futures_id,
                    "start_date": date_str,
                    "end_date": date_str,
                    "token": settings.FINMIND_API_TOKEN,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != 200 or not data.get("data"):
                logger.warning(f"{target_date} {futures_id} 無資料，跳過")
                continue

            # 只取目標日期
            rows = [r for r in data["data"] if r["date"] == date_str]
            if not rows:
                continue

            product_data = {}
            for row in rows:
                investor_name = row["institutional_investors"]
                key = INVESTOR_MAPPING.get(investor_name)
                if key:
                    product_data[key] = _parse_investor_row(row)

            if product_data:
                result[futures_id] = product_data

    if not result:
        raise RuntimeError(f"{target_date} 無任何期貨三大法人資料")

    # 印出摘要
    tx_foreign = result.get("TX", {}).get("foreign_investor", {}).get("net_oi_volume", 0)
    logger.info(f"已取得 {target_date} 期貨三大法人資料（{len(result)} 種商品），TX 外資淨OI: {tx_foreign:,}")
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


async def check_and_save_futures_institutional(
    db: AsyncIOMotorDatabase,
    target_date: date,
) -> dict:
    """
    抓取期貨三大法人未平倉餘額並存入獨立資料表。

    Returns:
        {"date": "...", "status": "fetched" | "skipped" | "closed", "detail": "..."}
    """
    date_str = target_date.strftime("%Y-%m-%d")
    fetch_collection = db[DAILY_MARKET_COLLECTION]
    data_collection = db[FUTURES_INSTITUTIONAL_COLLECTION]

    existing = await data_collection.find_one({"date": date_str})
    if existing:
        logger.info(f"{date_str} 期貨三大法人資料已存在，跳過")
        return {"date": date_str, "status": "skipped", "detail": "已抓取過"}

    fetch_doc = await fetch_collection.find_one({"date": date_str})
    if fetch_doc is None or fetch_doc.get("twse_is_open") is None:
        logger.warning(f"{date_str} 尚無開盤狀態資料，跳過期貨三大法人抓取")
        return {"date": date_str, "status": "skipped", "detail": "尚無開盤狀態"}

    if not fetch_doc.get("twse_is_open"):
        logger.info(f"{date_str} 休市，不抓取期貨三大法人資料")
        return {"date": date_str, "status": "closed", "detail": "休市日"}

    now = datetime.now(timezone.utc)
    try:
        inst_data = await fetch_futures_institutional_data(target_date)

        doc = {
            "date": date_str,
            **inst_data,
            "created_at": now,
            "updated_at": now,
        }
        await data_collection.insert_one(doc)

        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"futures_institutional": True, "updated_at": now}},
        )
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} futures_institutional: 抓取成功")

        tx_foreign = inst_data.get("TX", {}).get("foreign_investor", {}).get("net_oi_volume", 0)
        return {"date": date_str, "status": "fetched", "detail": f"TX外資淨OI: {tx_foreign:,}"}

    except Exception as e:
        error_msg = str(e)
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"futures_institutional": False, "updated_at": now}},
        )
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} futures_institutional: 抓取失敗 - {error_msg}")
        logger.error(f"{date_str} 期貨三大法人抓取失敗: {error_msg}")
        raise
