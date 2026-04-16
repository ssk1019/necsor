"""
排程引擎。

負責：
1. 從 MongoDB 載入排程設定
2. 計算下次執行時間（基於 cron 表達式）
3. 定期檢查並觸發到期任務
4. 處理重試邏輯與指數退避
5. 處理 misfire（超時未執行）策略
6. 記錄執行日誌
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

from croniter import croniter
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.scheduler import (
    JobExecutionLog,
    MisfirePolicy,
    ScheduleJob,
    TaskStatus,
)
from app.scheduler.constants import CHECK_INTERVAL, JOBS_COLLECTION, LOGS_COLLECTION
from app.scheduler.registry import get_task
from app.scheduler.utils import calc_next_run


class SchedulerEngine:
    """排程引擎主類別。"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """啟動排程引擎。"""
        if self._running:
            logger.warning("排程引擎已在運行中")
            return

        self._running = True
        # 啟動時先計算所有任務的下次執行時間
        await self._refresh_next_run_times()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("排程引擎已啟動")

    async def stop(self) -> None:
        """停止排程引擎。"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("排程引擎已停止")

    # ========================================
    # 主迴圈
    # ========================================

    async def _run_loop(self) -> None:
        """排程主迴圈，定期檢查到期任務。"""
        logger.info(f"排程迴圈啟動，檢查間隔: {CHECK_INTERVAL} 秒")
        while self._running:
            try:
                await self._check_and_execute()
            except Exception as e:
                logger.error(f"排程迴圈發生錯誤: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

    async def _check_and_execute(self) -> None:
        """檢查所有到期任務並執行。"""
        now = datetime.now(timezone.utc)
        collection = self._db[JOBS_COLLECTION]

        # 查詢已啟用且到期的任務
        cursor = collection.find({
            "enabled": True,
            "status": {"$nin": [TaskStatus.RUNNING, TaskStatus.DISABLED]},
            "next_run_at": {"$lte": now},
        })

        async for doc in cursor:
            job = ScheduleJob(**doc)
            asyncio.create_task(self._process_job(job, now))

    # ========================================
    # 任務處理
    # ========================================

    async def _process_job(self, job: ScheduleJob, trigger_time: datetime) -> None:
        """處理單一排程任務（含 misfire 判斷）。"""
        now = datetime.now(timezone.utc)

        # 檢查是否 misfire（超過容許延遲）
        if job.next_run_at:
            delay = (now - job.next_run_at).total_seconds()
            if delay > job.misfire_grace_seconds:
                await self._handle_misfire(job)
                return

        await self._execute_job(job)

    async def _execute_job(self, job: ScheduleJob, retry_attempt: int = 0) -> None:
        """
        執行任務，包含超時控制與重試邏輯。
        """
        collection = self._db[JOBS_COLLECTION]
        task_func = get_task(job.task_type)

        if task_func is None:
            logger.error(f"任務 '{job.job_id}' 的 task_type '{job.task_type}' 未註冊")
            await self._update_job_status(job, TaskStatus.FAILED)
            await self._save_log(job, TaskStatus.FAILED, retry_attempt,
                                 error_message=f"task_type '{job.task_type}' 未在 registry 中註冊")
            return

        # 標記為執行中
        status = TaskStatus.RETRYING if retry_attempt > 0 else TaskStatus.RUNNING
        await collection.update_one(
            {"job_id": job.job_id},
            {"$set": {"status": status, "current_retry_count": retry_attempt,
                      "updated_at": datetime.now(timezone.utc)}},
        )

        started_at = datetime.now(timezone.utc)
        try:
            # 帶超時執行任務
            result_summary = await asyncio.wait_for(
                task_func(job.task_params),
                timeout=job.timeout_seconds,
            )
            finished_at = datetime.now(timezone.utc)
            duration = (finished_at - started_at).total_seconds()

            # 成功 → 更新狀態、計算下次執行時間
            next_run = self._calc_next_run(job.cron_expression, job.timezone)
            await collection.update_one(
                {"job_id": job.job_id},
                {"$set": {
                    "status": TaskStatus.SUCCESS,
                    "last_run_at": started_at,
                    "last_success_at": finished_at,
                    "next_run_at": next_run,
                    "current_retry_count": 0,
                    "consecutive_failures": 0,
                    "updated_at": datetime.now(timezone.utc),
                }},
            )
            await self._save_log(job, TaskStatus.SUCCESS, retry_attempt,
                                 started_at=started_at, finished_at=finished_at,
                                 duration=duration, result_summary=result_summary)
            logger.info(f"任務 '{job.job_id}' 執行成功 (耗時 {duration:.1f}s)")

        except asyncio.TimeoutError:
            await self._on_failure(job, retry_attempt, started_at, "執行超時")

        except Exception as e:
            await self._on_failure(job, retry_attempt, started_at, str(e))

    # ========================================
    # 失敗與重試
    # ========================================

    async def _on_failure(
        self, job: ScheduleJob, retry_attempt: int,
        started_at: datetime, error_message: str,
    ) -> None:
        """任務失敗處理：決定是否重試或標記失敗。"""
        finished_at = datetime.now(timezone.utc)
        duration = (finished_at - started_at).total_seconds()
        collection = self._db[JOBS_COLLECTION]

        await self._save_log(job, TaskStatus.FAILED, retry_attempt,
                             started_at=started_at, finished_at=finished_at,
                             duration=duration, error_message=error_message)

        can_retry = retry_attempt < job.retry_policy.max_retries
        if can_retry:
            # 計算重試等待時間
            interval = job.retry_policy.retry_interval_seconds
            if job.retry_policy.exponential_backoff:
                interval = interval * (2 ** retry_attempt)

            logger.warning(
                f"任務 '{job.job_id}' 失敗 (第 {retry_attempt + 1} 次)，"
                f"{interval} 秒後重試: {error_message}"
            )

            await collection.update_one(
                {"job_id": job.job_id},
                {"$set": {"status": TaskStatus.RETRYING,
                          "updated_at": datetime.now(timezone.utc)}},
            )

            await asyncio.sleep(interval)
            await self._execute_job(job, retry_attempt + 1)
        else:
            # 重試次數用盡，標記失敗
            next_run = self._calc_next_run(job.cron_expression, job.timezone)
            new_failures = job.consecutive_failures + 1
            await collection.update_one(
                {"job_id": job.job_id},
                {"$set": {
                    "status": TaskStatus.FAILED,
                    "last_run_at": started_at,
                    "next_run_at": next_run,
                    "current_retry_count": 0,
                    "consecutive_failures": new_failures,
                    "updated_at": datetime.now(timezone.utc),
                }},
            )
            logger.error(
                f"任務 '{job.job_id}' 最終失敗 (已重試 {retry_attempt} 次，"
                f"連續失敗 {new_failures} 次): {error_message}"
            )

    # ========================================
    # Misfire 處理
    # ========================================

    async def _handle_misfire(self, job: ScheduleJob) -> None:
        """處理超時未執行的任務。"""
        collection = self._db[JOBS_COLLECTION]
        policy = job.misfire_policy

        if policy == MisfirePolicy.SKIP:
            # 跳過，直接計算下次執行時間
            next_run = self._calc_next_run(job.cron_expression, job.timezone)
            await collection.update_one(
                {"job_id": job.job_id},
                {"$set": {"status": TaskStatus.SKIPPED, "next_run_at": next_run,
                          "updated_at": datetime.now(timezone.utc)}},
            )
            await self._save_log(job, TaskStatus.SKIPPED, 0,
                                 error_message="超過容許延遲，依策略跳過")
            logger.info(f"任務 '{job.job_id}' misfire → 跳過")

        elif policy == MisfirePolicy.RUN_ONCE:
            # 補執行一次
            logger.info(f"任務 '{job.job_id}' misfire → 補執行一次")
            await self._execute_job(job)

        elif policy == MisfirePolicy.RUN_ALL:
            # 補執行所有錯過的次數
            missed = self._count_missed_runs(job)
            logger.info(f"任務 '{job.job_id}' misfire → 補執行 {missed} 次")
            for i in range(missed):
                await self._execute_job(job)

    def _count_missed_runs(self, job: ScheduleJob) -> int:
        """計算錯過了幾次執行。"""
        if not job.next_run_at:
            return 1
        now = datetime.now(timezone.utc)
        count = 0
        cron = croniter(job.cron_expression, job.next_run_at)
        while True:
            next_time = cron.get_next(datetime)
            if next_time.tzinfo is None:
                next_time = next_time.replace(tzinfo=timezone.utc)
            if next_time > now:
                break
            count += 1
            if count > 100:  # 安全上限
                break
        return max(count, 1)

    # ========================================
    # 工具方法
    # ========================================

    def _calc_next_run(self, cron_expression: str, tz: str = "Asia/Taipei") -> datetime:
        """根據 cron 表達式計算下次執行時間（回傳 UTC）。"""
        return calc_next_run(cron_expression, tz)

    async def _update_job_status(self, job: ScheduleJob, status: TaskStatus) -> None:
        """更新任務狀態。"""
        next_run = self._calc_next_run(job.cron_expression, job.timezone)
        await self._db[JOBS_COLLECTION].update_one(
            {"job_id": job.job_id},
            {"$set": {"status": status, "next_run_at": next_run,
                      "updated_at": datetime.now(timezone.utc)}},
        )

    async def _save_log(
        self, job: ScheduleJob, status: TaskStatus, retry_attempt: int,
        started_at: datetime | None = None, finished_at: datetime | None = None,
        duration: float | None = None, error_message: str | None = None,
        result_summary: str | None = None,
    ) -> None:
        """儲存執行紀錄到 MongoDB。"""
        log = JobExecutionLog(
            job_id=job.job_id,
            status=status,
            started_at=started_at or datetime.now(timezone.utc),
            finished_at=finished_at,
            duration_seconds=duration,
            retry_attempt=retry_attempt,
            error_message=error_message,
            result_summary=result_summary,
        )
        await self._db[LOGS_COLLECTION].insert_one(log.model_dump())

    async def _refresh_next_run_times(self) -> None:
        """啟動時重新計算所有啟用任務的下次執行時間。"""
        collection = self._db[JOBS_COLLECTION]
        cursor = collection.find({"enabled": True})
        count = 0
        async for doc in cursor:
            job = ScheduleJob(**doc)
            next_run = self._calc_next_run(job.cron_expression, job.timezone)
            await collection.update_one(
                {"job_id": job.job_id},
                {"$set": {"next_run_at": next_run, "status": TaskStatus.PENDING,
                          "updated_at": datetime.now(timezone.utc)}},
            )
            count += 1
        logger.info(f"已重新計算 {count} 個任務的下次執行時間")
