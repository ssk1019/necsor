"""
台股開休市日曆服務。

資料來源：證交所官方 API
https://www.twse.com.tw/rwd/zh/holidaySchedule/holidaySchedule

判斷邏輯：
1. 從證交所取得當年度開休市日期清單
2. 休市日清單中有明確標示哪些日期休市
3. 若當日為週六或週日 → 休市
4. 若當日在休市清單中 → 休市
5. 其餘 → 開盤

結果會快取在 Redis 中（以年度為 key），避免重複請求證交所。
"""

from datetime import datetime, timezone, date

import httpx
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.daily_market import DAILY_MARKET_COLLECTION
from app.utils.cache import cache_get, cache_set
from app.utils.time import now_log_prefix

# 證交所開休市日期 API
TWSE_HOLIDAY_API = "https://www.twse.com.tw/rwd/zh/holidaySchedule/holidaySchedule"

# Redis 快取 key 前綴與 TTL
CACHE_KEY_PREFIX = "twse_holidays"
CACHE_TTL = 86400  # 24 小時


async def fetch_twse_holidays(year: int) -> set[str]:
    """
    從證交所 API 取得指定年度的休市日期集合。

    Args:
        year: 西元年份

    Returns:
        休市日期集合，格式為 {"2026-01-01", "2026-02-15", ...}
    """
    cache_key = f"{CACHE_KEY_PREFIX}:{year}"

    # 先查 Redis 快取
    cached = await cache_get(cache_key)
    if cached is not None:
        logger.debug(f"從快取取得 {year} 年休市日期 ({len(cached)} 筆)")
        return set(cached)

    # 呼叫證交所 API
    logger.info(f"正在從證交所取得 {year} 年開休市日期...")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                TWSE_HOLIDAY_API,
                params={"response": "json", "queryYear": year},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"取得證交所開休市日期失敗: {e}")
        raise

    if data.get("stat") != "ok" or "data" not in data:
        logger.error(f"證交所 API 回傳異常: {data.get('stat')}")
        raise RuntimeError(f"證交所 API 回傳異常: {data}")

    # 解析休市日期
    # data["data"] 格式: [["2026-01-01", "中華民國開國紀念日", "依規定放假1日。"], ...]
    # 含「交易」字樣的是交易日，其餘為休市日
    holidays = set()
    for row in data["data"]:
        date_str = row[0]
        name = row[1]
        description = row[2]
        combined = name + description
        if "交易" in combined:
            continue
        holidays.add(date_str)

    # 存入 Redis 快取
    await cache_set(cache_key, list(holidays), expire=CACHE_TTL)
    logger.info(f"已取得 {year} 年休市日期 ({len(holidays)} 筆)，已快取")

    return holidays


async def check_twse_is_open(target_date: date) -> bool:
    """
    檢查指定日期台股是否有開盤。

    Args:
        target_date: 要檢查的日期

    Returns:
        True = 開盤, False = 休市
    """
    # 週六日一定休市
    if target_date.weekday() >= 5:
        return False

    # 取得該年度休市日期
    holidays = await fetch_twse_holidays(target_date.year)
    date_str = target_date.strftime("%Y-%m-%d")

    return date_str not in holidays


async def check_and_save_twse_open(
    db: AsyncIOMotorDatabase,
    target_date: date,
) -> dict:
    """
    檢查台股開盤狀態並存入 daily_market_fetch。

    如果該日期已有 twse_is_open 資料，則跳過不重複抓取。

    Args:
        db: MongoDB 資料庫實例
        target_date: 要檢查的日期

    Returns:
        {"date": "2026-04-18", "twse_is_open": True, "skipped": False}
    """
    date_str = target_date.strftime("%Y-%m-%d")
    collection = db[DAILY_MARKET_COLLECTION]

    # 檢查是否已抓取過
    existing = await collection.find_one(
        {"date": date_str, "twse_is_open": {"$ne": None}}
    )
    if existing:
        logger.info(f"{date_str} 台股開盤狀態已存在，跳過 (is_open={existing['twse_is_open']})")
        return {
            "date": date_str,
            "twse_is_open": existing["twse_is_open"],
            "skipped": True,
        }

    # 檢查開盤狀態
    is_open = await check_twse_is_open(target_date)
    now = datetime.now(timezone.utc)
    status_text = "開盤" if is_open else "休市"
    log_line = f"{now_log_prefix()} twse_is_open: {status_text} ({is_open})"

    # upsert：如果該日期文件不存在就建立，存在就更新
    await collection.update_one(
        {"date": date_str},
        {
            "$set": {
                "twse_is_open": is_open,
                "updated_at": now,
            },
            "$setOnInsert": {
                "date": date_str,
                "created_at": now,
                "fetch_log": "",
            },
        },
        upsert=True,
    )

    # 追加 fetch_log：在現有內容後面加一行
    # 先取得目前的 fetch_log 內容
    doc = await collection.find_one({"date": date_str})
    current_log = doc.get("fetch_log", "") if doc else ""
    separator = "\n" if current_log else ""
    new_log = f"{current_log}{separator}{log_line}"

    await collection.update_one(
        {"date": date_str},
        {"$set": {"fetch_log": new_log}},
    )

    logger.info(f"{date_str} 台股狀態: {status_text}")

    return {
        "date": date_str,
        "twse_is_open": is_open,
        "skipped": False,
    }
