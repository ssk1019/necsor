"""
台股加權指數與匯率資料模型。

獨立資料表，以日期為唯一主鍵。
資料來源：
- 加權指數：證交所 MI_5MINS_HIST API
- 匯率：台銀牌告匯率 fltxt

MongoDB 集合名稱: taiex_exchange
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

TAIEX_EXCHANGE_COLLECTION = "taiex_exchange"


class TaiexExchangeData(BaseModel):
    """台股加權指數與匯率"""

    date: str = Field(..., description="日期，格式 YYYY-MM-DD")

    # 加權指數
    taiex_open: Optional[float] = Field(default=None, description="加權指數開盤")
    taiex_high: Optional[float] = Field(default=None, description="加權指數最高")
    taiex_low: Optional[float] = Field(default=None, description="加權指數最低")
    taiex_close: Optional[float] = Field(default=None, description="加權指數收盤")

    # 美元兌台幣匯率（台銀即期買入/賣出）
    usd_twd_buy: Optional[float] = Field(default=None, description="美元即期買入")
    usd_twd_sell: Optional[float] = Field(default=None, description="美元即期賣出")

    # 時間戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


async def ensure_taiex_exchange_indexes(db) -> None:
    """建立唯一索引（date 降冪）。"""
    collection = db[TAIEX_EXCHANGE_COLLECTION]
    await collection.create_index([("date", -1)], unique=True)
