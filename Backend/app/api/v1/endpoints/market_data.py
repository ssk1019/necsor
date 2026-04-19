"""
市場資料查詢 API。
提供前端圖表所需的歷史資料。
"""

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db
from app.core.config import get_settings

router = APIRouter()


@router.get("/institutional/twse", summary="上市三大法人歷史資料")
async def get_twse_institutional(
    days: int = Query(default=None, ge=1, le=365, description="查詢天數"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """取得上市三大法人買賣金額歷史資料（依日期降冪）。"""
    settings = get_settings()
    limit = days or settings.CHART_DEFAULT_DAYS

    cursor = db["twse_institutional"].find(
        {}, {"_id": 0}
    ).sort("date", -1).limit(limit)

    data = await cursor.to_list(length=limit)
    # 反轉為升冪（前端圖表 x 軸由舊到新）
    data.reverse()

    return {"success": True, "data": data, "total": len(data)}


@router.get("/institutional/tpex", summary="上櫃三大法人歷史資料")
async def get_tpex_institutional(
    days: int = Query(default=None, ge=1, le=365, description="查詢天數"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """取得上櫃三大法人買賣金額歷史資料（依日期降冪）。"""
    settings = get_settings()
    limit = days or settings.CHART_DEFAULT_DAYS

    cursor = db["tpex_institutional"].find(
        {}, {"_id": 0}
    ).sort("date", -1).limit(limit)

    data = await cursor.to_list(length=limit)
    data.reverse()

    return {"success": True, "data": data, "total": len(data)}


@router.get("/margin", summary="融資融券餘額歷史資料")
async def get_margin_trading(
    days: int = Query(default=None, ge=1, le=365, description="查詢天數"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """取得融資融券餘額歷史資料（依日期升冪）。"""
    settings = get_settings()
    limit = days or settings.CHART_DEFAULT_DAYS

    cursor = db["margin_trading"].find(
        {}, {"_id": 0}
    ).sort("date", -1).limit(limit)

    data = await cursor.to_list(length=limit)
    data.reverse()

    return {"success": True, "data": data, "total": len(data)}


@router.get("/futures-oi", summary="台指期未平倉歷史資料")
async def get_futures_oi(
    days: int = Query(default=None, ge=1, le=365, description="查詢天數"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """取得台指期未平倉口數歷史資料（依日期升冪）。"""
    settings = get_settings()
    limit = days or settings.CHART_DEFAULT_DAYS

    cursor = db["futures_open_interest"].find(
        {},
        {"_id": 0, "date": 1, "total_volume": 1, "total_oi": 1,
         "front_month_close": 1, "front_month_oi": 1},
    ).sort("date", -1).limit(limit)

    data = await cursor.to_list(length=limit)
    data.reverse()

    return {"success": True, "data": data, "total": len(data)}


@router.get("/futures-institutional", summary="期貨三大法人未平倉歷史資料")
async def get_futures_institutional(
    days: int = Query(default=None, ge=1, le=365, description="查詢天數"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """取得期貨三大法人未平倉餘額歷史資料（依日期升冪）。"""
    settings = get_settings()
    limit = days or settings.CHART_DEFAULT_DAYS

    cursor = db["futures_institutional"].find(
        {}, {"_id": 0}
    ).sort("date", -1).limit(limit)

    data = await cursor.to_list(length=limit)
    data.reverse()

    return {"success": True, "data": data, "total": len(data)}
