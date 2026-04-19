"""
三大法人買賣金額統計服務（上櫃）。

資料來源：櫃買中心官方 API
https://www.tpex.org.tw/web/stock/3insti/3insti_summary/3itrdsum_result.php

注意：櫃買中心 API 使用民國年日期格式（如 115/04/17）。

抓取的數據存入獨立資料表 tpex_institutional（以日期為主鍵）。
抓取狀態旗標記錄在 daily_market_fetch.tpex_institutional。
抓取日誌記錄在 daily_market_fetch.fetch_log。
"""

from datetime import datetime, timezone, date

import httpx
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.daily_market import DAILY_MARKET_COLLECTION
from app.models.tpex_institutional import TPEX_INSTITUTIONAL_COLLECTION
from app.utils.time import now_log_prefix

# 櫃買中心三大法人買賣金額彙總 API
TPEX_3INSTI_API = "https://www.tpex.org.tw/web/stock/3insti/3insti_summary/3itrdsum_result.php"


def _to_roc_date(d: date) -> str:
    """將西元日期轉為民國年格式，例如 2026-04-17 → '115/04/17'"""
    roc_year = d.year - 1911
    return f"{roc_year}/{d.month:02d}/{d.day:02d}"


def _parse_amount(s: str) -> int:
    """將金額字串轉為整數，例如 '8,139,267,994' → 8139267994"""
    return int(s.replace(",", ""))


async def fetch_tpex_institutional_data(target_date: date) -> dict:
    """
    從櫃買中心 API 抓取指定日期的三大法人買賣金額彙總。

    Args:
        target_date: 要查詢的日期

    Returns:
        結構化的三大法人資料 dict

    Raises:
        RuntimeError: API 回傳異常或無資料
    """
    roc_date = _to_roc_date(target_date)

    logger.info(f"正在從櫃買中心抓取 {target_date} 上櫃三大法人買賣金額...")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            TPEX_3INSTI_API,
            params={"l": "zh-tw", "t": "D", "d": roc_date, "_": "1"},
        )
        resp.raise_for_status()
        data = resp.json()

    tables = data.get("tables", [])
    if not tables or not tables[0].get("data"):
        raise RuntimeError(f"{target_date} 無上櫃三大法人資料（可能非交易日）")

    table = tables[0]
    rows = table["data"]

    # 解析資料
    # rows 格式:
    # [["外資及陸資合計", "78,411,843,434", "72,766,093,448", "5,645,749,986"], ...]
    name_mapping = {
        "外資及陸資合計": "foreign_total",
        "　外資及陸資(不含自營商)": "foreign_investor",
        "　外資自營商": "foreign_dealer",
        "投信": "investment_trust",
        "自營商合計": "dealer_total",
        "　自營商(自行買賣)": "dealer_self",
        "　自營商(避險)": "dealer_hedge",
        "三大法人合計*": "total",
    }

    result = {}
    for row in rows:
        name = row[0]
        key = name_mapping.get(name)
        if key is None:
            continue
        result[key] = {
            "name": name.strip(),
            "buy": _parse_amount(row[1]),
            "sell": _parse_amount(row[2]),
            "diff": _parse_amount(row[3]),
        }

    total_diff = result.get("total", {}).get("diff", 0)
    logger.info(f"已取得 {target_date} 上櫃三大法人資料，合計買賣差額: {total_diff:,}")
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


async def check_and_save_tpex_institutional(
    db: AsyncIOMotorDatabase,
    target_date: date,
) -> dict:
    """
    抓取上櫃三大法人買賣金額並存入獨立資料表。

    前置檢查：
    1. 獨立表是否已有該日期資料 → 有則跳過
    2. daily_market_fetch 的 twse_is_open 是否為 True → 休市日不抓取

    Returns:
        {"date": "...", "status": "fetched" | "skipped" | "closed", "detail": "..."}
    """
    date_str = target_date.strftime("%Y-%m-%d")
    fetch_collection = db[DAILY_MARKET_COLLECTION]
    data_collection = db[TPEX_INSTITUTIONAL_COLLECTION]

    # 檢查獨立表是否已有資料
    existing = await data_collection.find_one({"date": date_str})
    if existing:
        logger.info(f"{date_str} 上櫃三大法人資料已存在，跳過")
        return {"date": date_str, "status": "skipped", "detail": "已抓取過"}

    # 檢查當日是否有開盤
    fetch_doc = await fetch_collection.find_one({"date": date_str})
    if fetch_doc is None or fetch_doc.get("twse_is_open") is None:
        logger.warning(f"{date_str} 尚無開盤狀態資料，跳過上櫃三大法人抓取")
        return {"date": date_str, "status": "skipped", "detail": "尚無開盤狀態"}

    if not fetch_doc.get("twse_is_open"):
        logger.info(f"{date_str} 休市，不抓取上櫃三大法人資料")
        return {"date": date_str, "status": "closed", "detail": "休市日"}

    # 抓取資料
    now = datetime.now(timezone.utc)
    try:
        institutional_data = await fetch_tpex_institutional_data(target_date)

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
            {"$set": {"tpex_institutional": True, "updated_at": now}},
        )

        # 追加 fetch_log
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} tpex_institutional: 抓取成功")

        total_diff = institutional_data.get("total", {}).get("diff", 0)
        logger.info(f"{date_str} 上櫃三大法人資料已儲存，合計買賣差額: {total_diff:,}")
        return {"date": date_str, "status": "fetched", "detail": f"合計差額: {total_diff:,}"}

    except Exception as e:
        error_msg = str(e)

        # 更新旗標為失敗
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"tpex_institutional": False, "updated_at": now}},
        )

        # 追加失敗紀錄
        await _append_fetch_log(db, date_str, f"{now_log_prefix()} tpex_institutional: 抓取失敗 - {error_msg}")

        logger.error(f"{date_str} 上櫃三大法人抓取失敗: {error_msg}")
        raise
