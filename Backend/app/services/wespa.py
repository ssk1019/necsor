"""
Wespa 股票資料爬取服務。

從 stock.wespai.com 多個頁面爬取股票資料表格，
以股票代號為 key 合併後存入 MongoDB。
"""

import io
from datetime import datetime, timezone

import httpx
import pandas as pd
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

# MongoDB 集合名稱
WESPA_COLLECTION = "wespa_stock_data"

# 資料來源 URL
WESPA_URLS = [
    "https://stock.wespai.com/p/42327",
    "https://stock.wespai.com/p/42307",
    "https://stock.wespai.com/p/42302",
    "https://stock.wespai.com/p/42305",
    "https://stock.wespai.com/p/42177",
    "https://stock.wespai.com/p/42179",
]

# 優先顯示的欄位順序
FRONT_COLUMNS = [
    "公司", "股價", "資本額(億)", "產業類型", "發行市場", "成交量", "本益比",
    "2年平均本益比", "4年平均本益比", "6年平均本益比", "9年平均本益比",
    "股價淨值比", "(月)累積營收年增率(%)", "(月-1)累積營收年增率(%)",
    "(月-2)累積營收年增率(%)",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


async def scrape_wespa_data(progress_callback=None) -> list[dict]:
    """
    從 Wespa 網站爬取並合併股票資料。

    Args:
        progress_callback: 可選的進度回呼函式 (current, total, message)

    Returns:
        合併後的股票資料列表（每筆為一個 dict）
    """
    all_dataframes = []
    total = len(WESPA_URLS)

    async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
        for i, url in enumerate(WESPA_URLS):
            if progress_callback:
                await progress_callback(i, total, f"正在抓取第 {i + 1}/{total} 個頁面...")

            try:
                logger.info(f"Wespa 抓取 {i + 1}/{total}: {url}")
                resp = await client.get(url)
                resp.raise_for_status()

                # 用 pandas 解析 HTML 表格
                tables = pd.read_html(io.StringIO(resp.text), attrs={"id": "example"})
                if tables:
                    df = tables[0]
                    df.rename(columns={df.columns[0]: "股票代號"}, inplace=True)
                    all_dataframes.append(df)
                else:
                    logger.warning(f"在 {url} 中找不到 id='example' 的表格")

            except Exception as e:
                logger.error(f"Wespa 抓取失敗 {url}: {e}")

    if not all_dataframes:
        raise RuntimeError("沒有成功爬取到任何資料")

    if progress_callback:
        await progress_callback(total, total, "正在合併資料...")

    # 合併所有 DataFrame
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    merged_df = combined_df.groupby("股票代號").first()

    # 重新排列欄位
    try:
        all_columns = merged_df.columns.tolist()
        remaining = [col for col in all_columns if col not in FRONT_COLUMNS]
        new_order = [col for col in FRONT_COLUMNS if col in all_columns] + remaining
        merged_df = merged_df[new_order]
    except Exception:
        pass

    # 轉為 list of dict
    merged_df.reset_index(inplace=True)
    # 將 NaN 轉為 None（JSON 相容）
    merged_df = merged_df.where(pd.notnull(merged_df), None)
    records = merged_df.to_dict(orient="records")

    # 額外清理：確保沒有 float('nan') 殘留
    import math
    for record in records:
        for key, val in record.items():
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                record[key] = None

    logger.info(f"Wespa 資料合併完成: {len(records)} 筆股票")
    return records


async def save_wespa_data(db: AsyncIOMotorDatabase, records: list[dict]) -> dict:
    """
    將 Wespa 資料存入 MongoDB（覆蓋舊資料）。

    Returns:
        {"count": 筆數, "fetched_at": 抓取時間}
    """
    collection = db[WESPA_COLLECTION]
    now = datetime.now(timezone.utc)

    # 清除舊資料，寫入新資料
    await collection.delete_many({})

    # 存入 metadata 文件
    meta = {
        "_type": "meta",
        "fetched_at": now,
        "count": len(records),
    }
    await collection.insert_one(meta)

    # 存入股票資料
    if records:
        docs = [{"_type": "stock", **r} for r in records]
        await collection.insert_many(docs)

    logger.info(f"Wespa 資料已儲存: {len(records)} 筆")
    return {"count": len(records), "fetched_at": now}


async def get_wespa_data(db: AsyncIOMotorDatabase) -> dict:
    """
    從 MongoDB 取得已儲存的 Wespa 資料。

    Returns:
        {"records": [...], "fetched_at": datetime | None, "count": int}
    """
    collection = db[WESPA_COLLECTION]

    # 取 metadata
    meta = await collection.find_one({"_type": "meta"})
    if not meta:
        return {"records": [], "fetched_at": None, "count": 0}

    # 取股票資料
    cursor = collection.find({"_type": "stock"}, {"_id": 0, "_type": 0})
    records = await cursor.to_list(length=5000)

    return {
        "records": records,
        "fetched_at": meta.get("fetched_at"),
        "count": len(records),
    }
