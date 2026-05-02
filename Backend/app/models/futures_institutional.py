"""
期貨三大法人未平倉餘額資料模型。

獨立資料表，以日期為唯一主鍵。
資料來源：FinMind API（TaiwanFuturesInstitutionalInvestors）。

記錄各類期貨（臺股/電子/金融/非金電）的三大法人未平倉餘額。

MongoDB 集合名稱: futures_institutional
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

# MongoDB 集合名稱
FUTURES_INSTITUTIONAL_COLLECTION = "futures_institutional"

# 支援的期貨商品
FUTURES_PRODUCTS = {
    "TX": "臺股期貨",
    "MTX": "小型臺指期貨",
    "TE": "電子期貨",
    "TF": "金融期貨",
    "XIF": "非金電期貨",
}


class FuturesInstitutionalItem(BaseModel):
    """單一法人的期貨交易與未平倉資料"""
    name: str = Field(..., description="法人名稱（自營商/投信/外資）")
    long_deal_volume: int = Field(default=0, description="多方交易口數")
    short_deal_volume: int = Field(default=0, description="空方交易口數")
    long_deal_amount: int = Field(default=0, description="多方交易金額")
    short_deal_amount: int = Field(default=0, description="空方交易金額")
    long_oi_volume: int = Field(default=0, description="多方未平倉口數")
    short_oi_volume: int = Field(default=0, description="空方未平倉口數")
    net_oi_volume: int = Field(default=0, description="未平倉淨口數（多-空）")
    long_oi_amount: int = Field(default=0, description="多方未平倉金額")
    short_oi_amount: int = Field(default=0, description="空方未平倉金額")
    net_oi_amount: int = Field(default=0, description="未平倉淨金額（多-空）")


class FuturesProductData(BaseModel):
    """單一期貨商品的三大法人資料"""
    dealer: Optional[FuturesInstitutionalItem] = Field(default=None, description="自營商")
    investment_trust: Optional[FuturesInstitutionalItem] = Field(default=None, description="投信")
    foreign_investor: Optional[FuturesInstitutionalItem] = Field(default=None, description="外資")


class FuturesInstitutionalData(BaseModel):
    """
    期貨三大法人未平倉餘額（含多種期貨商品）。

    date 欄位為唯一主鍵。
    各商品以 futures_id 為 key 存放。
    """
    date: str = Field(..., description="日期，格式 YYYY-MM-DD")

    # 各期貨商品
    TX: Optional[FuturesProductData] = Field(default=None, description="臺股期貨")
    MTX: Optional[FuturesProductData] = Field(default=None, description="小型臺指期貨")
    TE: Optional[FuturesProductData] = Field(default=None, description="電子期貨")
    TF: Optional[FuturesProductData] = Field(default=None, description="金融期貨")
    XIF: Optional[FuturesProductData] = Field(default=None, description="非金電期貨")

    # 時間戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


async def ensure_futures_institutional_indexes(db) -> None:
    """建立 futures_institutional 集合的唯一索引（date 降冪）。"""
    collection = db[FUTURES_INSTITUTIONAL_COLLECTION]
    await collection.create_index([("date", -1)], unique=True)
