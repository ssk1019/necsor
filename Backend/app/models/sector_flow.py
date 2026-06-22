"""
類股資金流向資料模型。

獨立資料表，以日期為唯一主鍵。
記錄各類股的三大法人買賣超股數彙總。

MongoDB 集合名稱: sector_flow
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

SECTOR_FLOW_COLLECTION = "sector_flow"


class SectorFlowData(BaseModel):
    """類股資金流向（某日所有類股的三大法人買賣超）"""
    date: str = Field(..., description="日期，格式 YYYY-MM-DD")
    sectors: list[dict] = Field(default_factory=list, description="各類股資料列表")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


async def ensure_sector_flow_indexes(db) -> None:
    """建立唯一索引（date 降冪）。"""
    collection = db[SECTOR_FLOW_COLLECTION]
    await collection.create_index([("date", -1)], unique=True)
