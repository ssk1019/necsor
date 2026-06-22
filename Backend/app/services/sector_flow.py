"""
類股資金流向服務。

從證交所 T86 API 按類股分別取得三大法人買賣超，彙總後得出各產業的資金流向。
資料來源：https://www.twse.com.tw/rwd/zh/fund/T86

注意：T86 回傳的是「股數」不是「金額」，但足以反映資金集中度。
"""

import asyncio
from datetime import date

import httpx
from loguru import logger

# 證交所 T86 API
TWSE_T86_API = "https://www.twse.com.tw/rwd/zh/fund/T86"

# 類股代碼與名稱對照
SECTOR_TYPES = {
    "01": "水泥",
    "02": "食品",
    "03": "塑膠",
    "04": "紡織纖維",
    "05": "電機機械",
    "06": "電器電纜",
    "21": "化學工業",
    "22": "生技醫療",
    "08": "玻璃陶瓷",
    "09": "造紙",
    "10": "鋼鐵",
    "11": "橡膠",
    "12": "汽車",
    "24": "半導體",
    "25": "電腦週邊",
    "26": "光電",
    "27": "通信網路",
    "28": "電子零組件",
    "29": "電子通路",
    "30": "資訊服務",
    "31": "其他電子",
    "14": "建材營造",
    "15": "航運",
    "16": "觀光餐旅",
    "17": "金融保險",
    "18": "貿易百貨",
    "23": "油電燃氣",
    "20": "其他",
}


def _parse_int(s: str) -> int:
    """解析逗號分隔的數字字串"""
    cleaned = s.replace(",", "").strip()
    if not cleaned or not cleaned.lstrip("-").isdigit():
        return 0
    return int(cleaned)


async def fetch_sector_flow(target_date: date) -> list[dict]:
    """
    取得指定日期各類股的三大法人買賣超彙總。

    Returns:
        [{"sector": "半導體", "foreign": 68653934, "trust": -69993605, "dealer": 6373166, "total": 5033495}, ...]
        按 total 由高到低排序。
    """
    date_str = target_date.strftime("%Y%m%d")
    results = []

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for code, name in SECTOR_TYPES.items():
            try:
                resp = await client.get(
                    TWSE_T86_API,
                    params={"date": date_str, "selectType": code, "response": "json"},
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("stat") != "OK" or not data.get("data"):
                    continue

                # 彙總該類股所有個股的買賣超
                # fields[0] = 證券代號, fields[1] = 證券名稱
                # fields[4] = 外資買賣超, fields[10] = 投信買賣超, fields[11] = 自營商買賣超, fields[18] = 三大法人合計
                total_foreign = 0
                total_trust = 0
                total_dealer = 0
                total_all = 0
                stocks = []

                for row in data["data"]:
                    total_foreign += _parse_int(row[4])
                    total_trust += _parse_int(row[10])
                    total_dealer += _parse_int(row[11])
                    total_all += _parse_int(row[18])
                    # 記錄個股代號與名稱
                    stock_code = row[0].strip() if row[0] else ""
                    stock_name = row[1].strip() if row[1] else ""
                    if stock_code:
                        stocks.append(f"{stock_code} {stock_name}")

                results.append({
                    "sector": name,
                    "sector_code": code,
                    "foreign": total_foreign,
                    "trust": total_trust,
                    "dealer": total_dealer,
                    "total": total_all,
                    "stocks": stocks,
                })

            except Exception as e:
                logger.warning(f"類股 {name}({code}) 取得失敗: {e}")
                continue

            # 避免請求過快
            await asyncio.sleep(0.3)

    # 按合計買賣超由高到低排序
    results.sort(key=lambda x: x["total"], reverse=True)

    logger.info(f"已取得 {target_date} 類股資金流向: {len(results)} 類股")
    return results


async def check_and_save_sector_flow(
    db,
    target_date: date,
) -> dict:
    """
    抓取類股資金流向並存入獨立資料表。冪等設計。

    Returns:
        {"date": "...", "status": "fetched" | "skipped" | "closed", "detail": "..."}
    """
    from datetime import datetime, timezone
    from app.models.daily_market import DAILY_MARKET_COLLECTION
    from app.models.sector_flow import SECTOR_FLOW_COLLECTION
    from app.utils.time import now_log_prefix

    date_str = target_date.strftime("%Y-%m-%d")
    fetch_collection = db[DAILY_MARKET_COLLECTION]
    data_collection = db[SECTOR_FLOW_COLLECTION]

    # 檢查是否已抓取
    existing = await data_collection.find_one({"date": date_str})
    if existing:
        logger.info(f"{date_str} 類股資金流向已存在，跳過")
        return {"date": date_str, "status": "skipped", "detail": "已抓取過"}

    # 檢查開盤狀態
    fetch_doc = await fetch_collection.find_one({"date": date_str})
    if fetch_doc is None or fetch_doc.get("twse_is_open") is None:
        return {"date": date_str, "status": "skipped", "detail": "尚無開盤狀態"}
    if not fetch_doc.get("twse_is_open"):
        return {"date": date_str, "status": "closed", "detail": "休市日"}

    now = datetime.now(timezone.utc)
    try:
        sectors = await fetch_sector_flow(target_date)
        if not sectors:
            raise RuntimeError(f"{date_str} 無類股資金流向資料")

        await data_collection.insert_one({
            "date": date_str,
            "sectors": sectors,
            "created_at": now,
            "updated_at": now,
        })

        # 更新旗標
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"sector_flow": True, "updated_at": now}},
        )

        # 追加 fetch_log
        from app.utils.time import now_log_prefix
        doc = await fetch_collection.find_one({"date": date_str})
        current_log = doc.get("fetch_log", "") if doc else ""
        separator = "\n" if current_log else ""
        log_line = f"{now_log_prefix()} sector_flow: 抓取成功 ({len(sectors)} 類股)"
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"fetch_log": f"{current_log}{separator}{log_line}"}},
        )

        logger.info(f"{date_str} 類股資金流向已儲存 ({len(sectors)} 類股)")
        return {"date": date_str, "status": "fetched", "detail": f"{len(sectors)} 類股"}

    except Exception as e:
        error_msg = str(e)
        await fetch_collection.update_one(
            {"date": date_str},
            {"$set": {"sector_flow": False, "updated_at": now}},
        )
        logger.error(f"{date_str} 類股資金流向抓取失敗: {error_msg}")
        raise
