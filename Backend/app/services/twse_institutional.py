"""
三大法人買賣金額統計服務（上市）。

資料來源：證交所官方 API
https://www.twse.com.tw/rwd/zh/fund/BFI82U

抓取的數據存入獨立資料表 twse_institutional（以日期為主鍵）。
抓取狀態旗標記錄在 daily_market_fetch.twse_institutional。
抓取日誌記錄在 daily_market_fetch.fetch_log。
"""

from datetime import datetime, timezone, date

import httpx
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.daily_market import DAILY_MARKET_COLLECTION
from app.models.twse_institutional import TWSE_INSTITUTIONAL_COLLECTION
from app.utils.time import now_log_prefix

# 證交所三大法人買賣金額 API
TWSE_BFI82U_API = "https://www.twse.com.tw/rwd/zh/fund/BFI82U"


def _parse_amount(s: str) -> int:
    """將證交所回傳的金額字串轉為整數，例如 '8,139,267,994' → 8139267994"""
    return int(s.replace(",", ""))


async def fetch_institutional_data(target_date: date) -> dict:
    """
    從證交所 API 抓取指定日期的三大法人買賣金額。

    Args:
        target_date: 要查詢的日期

    Returns:
        結構化的三大法人資料 dict

    Raises:
        RuntimeError: API 回傳異常或無資料
    """
    date_str = target_date.strftime("%Y%m%d")

    logger.info(f"正在從證交所抓取 {target_date} 三大法人買賣金額...")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            TWSE_BFI82U_API,
            params={"type": "day", "dayDate": date_str, "response": "json"},
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("stat") != "OK" or "data" not in data:
        raise RuntimeError(f"證交所 API 回傳異常: stat={data.get('stat')}")

    if not data["data"]:
        raise RuntimeError(f"{target_date} 無三大法人資料（可能非交易日）")

    # 解析資料
    name_mapping = {
        "自營商(自行買賣)": "dealer_self",
        "自營商(避險)": "dealer_hedge",
        "投信": "investment_trust",
        "外資及陸資(不含外資自營商)": "foreign_investor",
        "外資自營商": "foreign_dealer",
        "合計": "total",
    }

    result = {}
    for row in data["data"]:
        name = row[0].strip()
        key = name_mapping.get(name)
        if key is None:
            continue
        result[key] = {
            "name": name,
            "buy": _parse_amount(row[1]),
            "sell": _parse_amount(row[2]),
            "diff": _parse_amount(row[3]),
        }

    total_diff = result.get("total", {}).get("diff", 0)
    logger.info(f"已取得 {target_date} 三大法人資料，合計買賣差額: {total_diff:,}")
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


async def check_and_save_institutional(
    db: AsyncIOMotorDatabase,
    target_date: date,
) -> dict:
    """
    抓取三大法人買賣金額並存入獨立資料表。

    前置檢查：
    1. 獨立表是否已有該日期資料 → 有則跳過
    2. daily_market_fetch 的 twse_is_open 是否為 True → 休市日不抓取

    成功時：
    - 數據寫入 twse_institutional 集合
    - daily_market_fetch.twse_institutional 設為 True
    - fetch_log 追加成功紀錄

    失敗時：
    - daily_market_fetch.twse_institutional 設為 False
    - fetch_log 追加失敗紀錄

    Returns:
        {"date": "...", "status": "fetched" | "skipped" | "closed", "detail": "..."}
    """
    date_str = target_date.strftime("%Y-%m-%d")
    fetch_collection = db[DAILY_MARKET_COLLECTION]
    data_collection = db[TWSE_INSTITUTIONAL_COLLECTION]

    # 檢查獨立表是否已有資料
    existing = await data_collection.find_one({"date": date_str})
    if existing:
        logger.info(f"{date_str} 三大法人資料已存在，跳過")
        return {"date": date_str, "status": "skipped", "detail": "已抓取過"}

    # 檢查當日是否有開盤
    fetch_doc = await fetch_collection.find_one({"date": date_str})
    if fetch_doc is None or fetch_doc.get("twse_is_open") is None:
        logger.warning(f"{date_str} 尚無開盤狀態資料，跳過三大法人抓取")
        return {"date": date_str, "status": "skipped", "detail": "尚無開盤狀態"}

    if not fetch_doc.get("twse_is_open"):
        logger.info(f"{date_str} 休市，不抓取三大法人資料")
        return {"date": date_str, "status": "closed", "detail": "休市日"}

    # 抓取資料
    now = datetime.now(timezone.utc)
    try:
        institutional_data = await fetch_institutional_data(target_date)

        # 寫入獨立資料表
        doc = {
            "date": date_str,
            **institutional_data,
            "created_at": now,
            "updated_at": now,
        }
        await data_collection.insert_one(doc)

        # 更新 daily_market_fetch 旗標
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"twse_institutional": True, "updated_at": now}},
        )

        # 追加 fetch_log
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} twse_institutional: 抓取成功")

        total_diff = institutional_data.get("total", {}).get("diff", 0)
        logger.info(f"{date_str} 三大法人資料已儲存，合計買賣差額: {total_diff:,}")
        return {"date": date_str, "status": "fetched", "detail": f"合計差額: {total_diff:,}"}

    except Exception as e:
        error_msg = str(e)

        # 更新 daily_market_fetch 旗標為失敗
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"twse_institutional": False, "updated_at": now}},
        )

        # 追加失敗紀錄到 fetch_log
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} twse_institutional: 抓取失敗 - {error_msg}")

        logger.error(f"{date_str} 三大法人抓取失敗: {error_msg}")
        raise
