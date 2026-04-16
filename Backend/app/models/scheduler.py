"""
排程器資料模型。

定義排程任務在 MongoDB 中的文件結構，包含：
- 排程設定（cron 表達式、時區）
- 重試策略（次數、間隔、指數退避）
- 超時與補執行策略
- 執行狀態追蹤
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任務執行狀態"""
    PENDING = "pending"          # 等待執行
    RUNNING = "running"          # 執行中
    SUCCESS = "success"          # 執行成功
    FAILED = "failed"            # 執行失敗
    RETRYING = "retrying"        # 重試中
    SKIPPED = "skipped"          # 已跳過（超時未補執行）
    DISABLED = "disabled"        # 已停用


class RetryPolicy(BaseModel):
    """重試策略設定"""
    max_retries: int = Field(default=3, ge=0, description="最大重試次數，0 表示不重試")
    retry_interval_seconds: int = Field(default=60, ge=1, description="重試間隔（秒）")
    exponential_backoff: bool = Field(default=False, description="是否啟用指數退避")


class MisfirePolicy(str, Enum):
    """超時未執行的處理策略"""
    RUN_ONCE = "run_once"        # 補執行一次（不管錯過幾次）
    SKIP = "skip"                # 跳過，等下次排程
    RUN_ALL = "run_all"          # 補執行所有錯過的次數


class ScheduleJob(BaseModel):
    """
    排程任務定義。

    cron 表達式範例：
    - "0 9 * * 1"       → 每週一 09:00
    - "0 9 * * 1-5"     → 每週一到五 09:00
    - "0 0 1 * *"       → 每月 1 號 00:00
    - "*/30 * * * *"    → 每 30 分鐘
    - "0 9 15 * *"      → 每月 15 號 09:00
    """

    # === 基本資訊 ===
    job_id: str = Field(..., description="任務唯一識別碼，例如 'crawler_stock_daily'")
    name: str = Field(..., description="任務名稱（顯示用）")
    description: str = Field(default="", description="任務說明")
    task_type: str = Field(..., description="對應的任務函式名稱（需在 task registry 中註冊）")
    task_params: dict = Field(default_factory=dict, description="傳給任務函式的參數")

    # === 排程設定 ===
    cron_expression: str = Field(..., description="Cron 表達式（分 時 日 月 週）")
    timezone: str = Field(default="Asia/Taipei", description="時區")
    enabled: bool = Field(default=True, description="是否啟用")

    # === 重試策略 ===
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy, description="重試策略")

    # === 超時設定 ===
    timeout_seconds: int = Field(default=300, ge=1, description="任務執行超時時間（秒）")
    misfire_policy: MisfirePolicy = Field(
        default=MisfirePolicy.RUN_ONCE,
        description="超時未執行的處理策略",
    )
    misfire_grace_seconds: int = Field(
        default=600, ge=0,
        description="容許延遲秒數，超過此值才視為 misfire",
    )

    # === 執行狀態 ===
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="目前狀態")
    last_run_at: Optional[datetime] = Field(default=None, description="上次執行時間")
    next_run_at: Optional[datetime] = Field(default=None, description="下次預計執行時間")
    last_success_at: Optional[datetime] = Field(default=None, description="上次成功時間")
    current_retry_count: int = Field(default=0, ge=0, description="目前重試次數")
    consecutive_failures: int = Field(default=0, ge=0, description="連續失敗次數")

    # === 時間戳 ===
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobExecutionLog(BaseModel):
    """
    任務執行紀錄。
    每次執行（含重試）都會產生一筆紀錄。
    """
    job_id: str = Field(..., description="對應的排程任務 ID")
    status: TaskStatus = Field(..., description="執行結果")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default=None, description="結束時間")
    duration_seconds: Optional[float] = Field(default=None, description="執行耗時（秒）")
    retry_attempt: int = Field(default=0, ge=0, description="第幾次重試（0 = 首次執行）")
    error_message: Optional[str] = Field(default=None, description="錯誤訊息")
    result_summary: Optional[str] = Field(default=None, description="執行結果摘要")
