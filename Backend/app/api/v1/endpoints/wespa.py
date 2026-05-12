"""
Wespa 股票資料 API。
"""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db
from app.services.wespa import scrape_wespa_data, save_wespa_data, get_wespa_data

router = APIRouter()


@router.get("", summary="取得已儲存的 Wespa 資料")
async def get_data(db: AsyncIOMotorDatabase = Depends(get_db)):
    """取得上次抓取的 Wespa 股票資料。"""
    import math

    result = await get_wespa_data(db)

    # 清理 NaN 值（MongoDB 可能存有 NaN）
    for record in result["records"]:
        for key, val in record.items():
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                record[key] = None

    return {
        "success": True,
        "data": result["records"],
        "count": result["count"],
        "fetched_at": result["fetched_at"],
    }


@router.post("/refresh", summary="重新抓取 Wespa 資料")
async def refresh_data(db: AsyncIOMotorDatabase = Depends(get_db)):
    """重新從 Wespa 網站爬取資料並儲存。"""
    records = await scrape_wespa_data()
    result = await save_wespa_data(db, records)
    return {
        "success": True,
        "message": f"已抓取 {result['count']} 筆股票資料",
        "count": result["count"],
        "fetched_at": result["fetched_at"],
    }
