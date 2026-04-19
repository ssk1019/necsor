"""
每日市場抓取資料模型。

以日期為主鍵（唯一索引）的共用資料表，各種每日抓取的資料都存在這裡。
每個抓取項目對應一個欄位，已抓取的欄位不會重複抓取。
所有抓取紀錄統一寫入 fetch_log 欄位。

MongoDB 集合名稱: daily_market_fetch
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

# MongoDB 集合名稱
DAILY_MARKET_COLLECTION = "daily_market_fetch"


class DailyMarketFetch(BaseModel):
    """
    每日市場抓取資料。

    date 欄位為唯一主鍵（需建立 unique index）。
    各抓取項目以獨立欄位存放，欄位為 None 表示尚未抓取。
    fetch_log 記錄所有抓取操作的日誌。
    """

    # 主鍵（唯一索引）
    date: str = Field(..., description="日期，格式 YYYY-MM-DD（唯一主鍵）")

    # === 台股開盤狀態 ===
    twse_is_open: Optional[bool] = Field(
        default=None,
        description="台股當日是否有開盤（None 表示尚未檢查）",
    )

    # === 三大法人買賣金額（上市） ===
    twse_institutional: Optional[bool] = Field(
        default=None,
        description="三大法人資料是否已抓取（None=未抓, True=已抓, False=抓取失敗）",
    )

    # === 三大法人買賣金額（上櫃） ===
    tpex_institutional: Optional[bool] = Field(
        default=None,
        description="上櫃三大法人資料是否已抓取（None=未抓, True=已抓, False=抓取失敗）",
    )

    # === 融資融券餘額 ===
    margin_trading: Optional[bool] = Field(
        default=None,
        description="融資融券餘額是否已抓取（None=未抓, True=已抓, False=抓取失敗）",
    )

    # === 台指期未平倉 ===
    futures_oi: Optional[bool] = Field(
        default=None,
        description="台指期未平倉是否已抓取（None=未抓, True=已抓, False=抓取失敗）",
    )

    # === 期貨三大法人未平倉 ===
    futures_institutional: Optional[bool] = Field(
        default=None,
        description="期貨三大法人未平倉是否已抓取（None=未抓, True=已抓, False=抓取失敗）",
    )

    # === 未來擴充欄位（範例） ===
    # tpex_is_open: Optional[bool] = None
    # exchange_rate_usd_twd: Optional[float] = None

    # === 抓取紀錄 ===
    fetch_log: str = Field(
        default="",
        description="抓取紀錄日誌，每筆一行，格式: [YYYY-MM-DD HH:MM:SS] 訊息",
    )

    # === 時間戳 ===
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


async def ensure_daily_market_indexes(db) -> None:
    """建立 daily_market_fetch 集合的唯一索引（date 降冪）。應在應用啟動時呼叫。"""
    collection = db[DAILY_MARKET_COLLECTION]

    # 移除舊的升冪索引（如果存在），改建降冪索引
    existing = await collection.index_information()
    if "date_1" in existing:
        await collection.drop_index("date_1")

    await collection.create_index([("date", -1)], unique=True)
