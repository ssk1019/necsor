"""
融資融券餘額統計資料模型。

獨立資料表，以日期為唯一主鍵。
資料來源：證交所 MI_MARGN API（selectType=MS 彙總）。

MongoDB 集合名稱: margin_trading
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

# MongoDB 集合名稱
MARGIN_TRADING_COLLECTION = "margin_trading"


class MarginItem(BaseModel):
    """融資或融券單項資料"""
    buy: int = Field(..., description="買進")
    sell: int = Field(..., description="賣出")
    cash_repay: int = Field(..., description="現金(券)償還")
    prev_balance: int = Field(..., description="前日餘額")
    today_balance: int = Field(..., description="今日餘額")


class MarginTradingData(BaseModel):
    """
    融資融券餘額統計。

    date 欄位為唯一主鍵（需建立 unique index）。
    """

    # 主鍵（唯一索引，降冪）
    date: str = Field(..., description="日期，格式 YYYY-MM-DD")

    # 融資（交易單位）
    margin_buy: Optional[MarginItem] = Field(default=None, description="融資（交易單位）")
    # 融券（交易單位）
    short_sell: Optional[MarginItem] = Field(default=None, description="融券（交易單位）")
    # 融資金額（仟元）
    margin_buy_amount: Optional[MarginItem] = Field(default=None, description="融資金額（仟元）")

    # 時間戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


async def ensure_margin_trading_indexes(db) -> None:
    """建立 margin_trading 集合的唯一索引（date 降冪）。"""
    collection = db[MARGIN_TRADING_COLLECTION]
    await collection.create_index([("date", -1)], unique=True)
