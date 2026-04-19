"""
三大法人買賣金額統計資料模型（上市）。

獨立資料表，以日期為唯一主鍵。
資料來源：證交所 BFI82U API。

MongoDB 集合名稱: twse_institutional
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

# MongoDB 集合名稱
TWSE_INSTITUTIONAL_COLLECTION = "twse_institutional"


class InstitutionalItem(BaseModel):
    """單一法人買賣金額"""
    name: str = Field(..., description="法人名稱")
    buy: int = Field(..., description="買進金額")
    sell: int = Field(..., description="賣出金額")
    diff: int = Field(..., description="買賣差額")


class TwseInstitutionalData(BaseModel):
    """
    三大法人買賣金額統計（上市）。

    date 欄位為唯一主鍵（需建立 unique index）。
    """

    # 主鍵（唯一索引，降冪）
    date: str = Field(..., description="日期，格式 YYYY-MM-DD")

    # 各法人資料
    dealer_self: Optional[InstitutionalItem] = Field(default=None, description="自營商(自行買賣)")
    dealer_hedge: Optional[InstitutionalItem] = Field(default=None, description="自營商(避險)")
    investment_trust: Optional[InstitutionalItem] = Field(default=None, description="投信")
    foreign_investor: Optional[InstitutionalItem] = Field(default=None, description="外資及陸資(不含外資自營商)")
    foreign_dealer: Optional[InstitutionalItem] = Field(default=None, description="外資自營商")
    total: Optional[InstitutionalItem] = Field(default=None, description="合計")

    # 時間戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


async def ensure_twse_institutional_indexes(db) -> None:
    """建立 twse_institutional 集合的唯一索引（date 降冪）。"""
    collection = db[TWSE_INSTITUTIONAL_COLLECTION]
    await collection.create_index([("date", -1)], unique=True)
