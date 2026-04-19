"""
台指期未平倉口數資料模型。

獨立資料表，以日期為唯一主鍵。
資料來源：FinMind API（TaiwanFuturesDaily, data_id=TX）。

儲存每日各合約月份的未平倉口數、成交量、收盤價等資訊。

MongoDB 集合名稱: futures_open_interest
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

# MongoDB 集合名稱
FUTURES_OI_COLLECTION = "futures_open_interest"


class FuturesContractItem(BaseModel):
    """單一合約月份的期貨資料"""
    contract_date: str = Field(..., description="合約月份，如 202605")
    open: float = Field(default=0, description="開盤價")
    high: float = Field(default=0, description="最高價")
    low: float = Field(default=0, description="最低價")
    close: float = Field(default=0, description="收盤價")
    volume: int = Field(default=0, description="成交量")
    open_interest: int = Field(default=0, description="未平倉口數")
    settlement_price: float = Field(default=0, description="結算價")
    trading_session: str = Field(default="", description="交易時段")


class FuturesOIData(BaseModel):
    """
    台指期未平倉口數資料。

    date 欄位為唯一主鍵。
    contracts 存放各合約月份的明細。
    彙總欄位方便查詢。
    """

    date: str = Field(..., description="日期，格式 YYYY-MM-DD")

    # 彙總（所有合約加總）
    total_volume: int = Field(default=0, description="總成交量")
    total_oi: int = Field(default=0, description="總未平倉口數")
    front_month_close: float = Field(default=0, description="近月合約收盤價")
    front_month_oi: int = Field(default=0, description="近月合約未平倉口數")

    # 各合約明細
    contracts: list[dict] = Field(default_factory=list, description="各合約月份明細")

    # 時間戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


async def ensure_futures_oi_indexes(db) -> None:
    """建立 futures_open_interest 集合的唯一索引（date 降冪）。"""
    collection = db[FUTURES_OI_COLLECTION]
    await collection.create_index([("date", -1)], unique=True)
