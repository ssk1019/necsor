"""
排程管理 API 端點。

提供排程任務的 CRUD 操作、手動觸發、查詢執行紀錄等功能。
"""

from datetime import datetime, timezone

from croniter import croniter
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db
from app.models.scheduler import ScheduleJob, TaskStatus
from app.schemas.scheduler import JobCreateRequest, JobUpdateRequest
from app.scheduler.constants import JOBS_COLLECTION, LOGS_COLLECTION
from app.scheduler.registry import get_all_task_types, get_task
from app.scheduler.utils import calc_next_run

router = APIRouter()


@router.get("", summary="取得所有排程任務")
async def list_jobs(
    enabled_only: bool = False,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """列出所有排程任務。"""
    query = {"enabled": True} if enabled_only else {}
    cursor = db[JOBS_COLLECTION].find(query, {"_id": 0})
    jobs = await cursor.to_list(length=500)
    return {"success": True, "data": jobs, "total": len(jobs)}


@router.get("/task-types", summary="取得所有已註冊的任務類型")
async def list_task_types():
    """列出所有可用的 task_type（已在 registry 中註冊的）。"""
    return {"success": True, "data": get_all_task_types()}


@router.get("/{job_id}", summary="取得單一排程任務")
async def get_job(
    job_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """根據 job_id 取得排程任務詳情。"""
    doc = await db[JOBS_COLLECTION].find_one(
        {"job_id": job_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail=f"找不到任務: {job_id}")
    return {"success": True, "data": doc}


@router.post("", summary="建立排程任務", status_code=201)
async def create_job(
    req: JobCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """建立新的排程任務。"""
    # 驗證 cron 表達式
    if not croniter.is_valid(req.cron_expression):
        raise HTTPException(status_code=400, detail=f"無效的 cron 表達式: {req.cron_expression}")

    # 驗證 task_type 已註冊
    if get_task(req.task_type) is None:
        available = get_all_task_types()
        raise HTTPException(
            status_code=400,
            detail=f"task_type '{req.task_type}' 未註冊。可用類型: {available}",
        )

    # 檢查 job_id 是否重複
    existing = await db[JOBS_COLLECTION].find_one({"job_id": req.job_id})
    if existing:
        raise HTTPException(status_code=409, detail=f"job_id '{req.job_id}' 已存在")

    # 建立任務文件
    job = ScheduleJob(**req.model_dump())
    # 計算下次執行時間
    job.next_run_at = calc_next_run(job.cron_expression, job.timezone)

    await db[JOBS_COLLECTION].insert_one(job.model_dump())
    return {"success": True, "message": f"任務 '{req.job_id}' 已建立", "data": job.model_dump()}


@router.put("/{job_id}", summary="更新排程任務")
async def update_job(
    job_id: str,
    req: JobUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """更新排程任務設定（僅更新有提供的欄位）。"""
    update_data = req.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="沒有提供任何更新欄位")

    # 驗證 cron 表達式（如果有更新）
    if "cron_expression" in update_data:
        if not croniter.is_valid(update_data["cron_expression"]):
            raise HTTPException(status_code=400, detail="無效的 cron 表達式")

    # 驗證 task_type（如果有更新）
    if "task_type" in update_data:
        if get_task(update_data["task_type"]) is None:
            raise HTTPException(status_code=400, detail=f"task_type '{update_data['task_type']}' 未註冊")

    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await db[JOBS_COLLECTION].update_one(
        {"job_id": job_id}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"找不到任務: {job_id}")

    return {"success": True, "message": f"任務 '{job_id}' 已更新"}


@router.delete("/{job_id}", summary="刪除排程任務")
async def delete_job(
    job_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """刪除排程任務（同時刪除執行紀錄）。"""
    result = await db[JOBS_COLLECTION].delete_one({"job_id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"找不到任務: {job_id}")

    # 同時清除執行紀錄
    await db[LOGS_COLLECTION].delete_many({"job_id": job_id})
    return {"success": True, "message": f"任務 '{job_id}' 及其紀錄已刪除"}


@router.post("/{job_id}/trigger", summary="手動觸發任務")
async def trigger_job(
    job_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """手動立即觸發一次排程任務（不影響正常排程）。"""
    doc = await db[JOBS_COLLECTION].find_one({"job_id": job_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"找不到任務: {job_id}")

    job = ScheduleJob(**doc)
    task_func = get_task(job.task_type)
    if task_func is None:
        raise HTTPException(status_code=400, detail=f"task_type '{job.task_type}' 未註冊")

    # 非同步執行，不阻塞回應
    import asyncio
    from app.scheduler.engine import SchedulerEngine
    engine = SchedulerEngine(db)
    asyncio.create_task(engine._execute_job(job))

    return {"success": True, "message": f"任務 '{job_id}' 已觸發執行"}


@router.get("/{job_id}/logs", summary="查詢任務執行紀錄")
async def get_job_logs(
    job_id: str,
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """查詢指定任務的執行紀錄（依時間倒序）。"""
    cursor = db[LOGS_COLLECTION].find(
        {"job_id": job_id}, {"_id": 0}
    ).sort("started_at", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    return {"success": True, "data": logs, "total": len(logs)}
