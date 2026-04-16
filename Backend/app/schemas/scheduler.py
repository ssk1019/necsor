"""
排程器相關的請求 / 回應 Schema。
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.scheduler import MisfirePolicy, RetryPolicy


class JobCreateRequest(BaseModel):
    """建立排程任務的請求"""
    job_id: str = Field(..., description="任務唯一識別碼")
    name: str = Field(..., description="任務名稱")
    description: str = Field(default="", description="任務說明")
    task_type: str = Field(..., description="任務類型（需已註冊）")
    task_params: dict = Field(default_factory=dict, description="任務參數")
    cron_expression: str = Field(..., description="Cron 表達式")
    timezone: str = Field(default="Asia/Taipei", description="時區")
    enabled: bool = Field(default=True, description="是否啟用")
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_seconds: int = Field(default=300, ge=1, description="超時秒數")
    misfire_policy: MisfirePolicy = Field(default=MisfirePolicy.RUN_ONCE)
    misfire_grace_seconds: int = Field(default=600, ge=0)


class JobUpdateRequest(BaseModel):
    """更新排程任務的請求（所有欄位皆為可選）"""
    name: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    task_params: Optional[dict] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    enabled: Optional[bool] = None
    retry_policy: Optional[RetryPolicy] = None
    timeout_seconds: Optional[int] = Field(default=None, ge=1)
    misfire_policy: Optional[MisfirePolicy] = None
    misfire_grace_seconds: Optional[int] = Field(default=None, ge=0)
