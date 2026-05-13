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


# === 篩選預設 ===

PRESETS_COLLECTION = "wespa_filter_presets"


@router.get("/presets", summary="取得所有篩選預設")
async def get_presets(db: AsyncIOMotorDatabase = Depends(get_db)):
    """取得所有已儲存的篩選預設。"""
    cursor = db[PRESETS_COLLECTION].find({}, {"_id": 0}).sort("created_at", -1)
    presets = await cursor.to_list(length=100)
    return {"success": True, "data": presets}


@router.post("/presets", summary="儲存篩選預設", status_code=201)
async def save_preset(
    preset: dict,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """儲存或覆蓋篩選預設（以 name 為 key）。"""
    from datetime import datetime, timezone

    name = preset.get("name")
    if not name:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="預設名稱不可為空")

    now = datetime.now(timezone.utc)
    doc = {**preset, "updated_at": now}

    # upsert：同名覆蓋
    result = await db[PRESETS_COLLECTION].update_one(
        {"name": name},
        {"$set": doc, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )

    return {"success": True, "message": f"已儲存預設「{name}」"}


@router.delete("/presets/{name}", summary="刪除篩選預設")
async def delete_preset(
    name: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """刪除指定名稱的篩選預設。"""
    result = await db[PRESETS_COLLECTION].delete_one({"name": name})
    if result.deleted_count == 0:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"找不到預設: {name}")
    return {"success": True, "message": f"已刪除預設「{name}」"}
