"""
補足近期所有排程任務缺漏的資料。

直接呼叫各排程任務函式，利用內建的回溯補抓機制自動補齊。
不需要後端服務運行，獨立執行即可。

用法（從 Backend/ 目錄執行）：
    python scripts/backfill_all.py
    python scripts/backfill_all.py --days 10   # 自訂回溯天數
"""

import sys
import os

# 將 Backend 目錄加入 Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
from loguru import logger

from app.core.database import connect_mongodb, connect_redis, close_mongodb, close_redis, get_database
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.models.daily_market import ensure_daily_market_indexes
from app.models.twse_institutional import ensure_twse_institutional_indexes
from app.models.tpex_institutional import ensure_tpex_institutional_indexes
from app.models.margin_trading import ensure_margin_trading_indexes
from app.models.futures_oi import ensure_futures_oi_indexes
from app.models.futures_institutional import ensure_futures_institutional_indexes
from app.models.taiex_exchange import ensure_taiex_exchange_indexes
from app.models.sector_flow import ensure_sector_flow_indexes


async def main(override_days: int | None = None):
    setup_logging()
    settings = get_settings()

    # 如果有指定天數，臨時覆蓋所有回溯設定
    if override_days:
        settings.TWSE_OPEN_CHECK_BACKFILL_DAYS = override_days
        settings.TWSE_INSTITUTIONAL_BACKFILL_DAYS = override_days
        settings.TPEX_INSTITUTIONAL_BACKFILL_DAYS = override_days
        settings.MARGIN_TRADING_BACKFILL_DAYS = override_days
        settings.FUTURES_OI_BACKFILL_DAYS = override_days
        settings.FUTURES_INSTITUTIONAL_BACKFILL_DAYS = override_days
        settings.TAIEX_EXCHANGE_BACKFILL_DAYS = override_days
        logger.info(f"回溯天數覆蓋為: {override_days} 天")

    await connect_mongodb()
    await connect_redis()
    db = get_database()

    # 建立索引
    await ensure_daily_market_indexes(db)
    await ensure_twse_institutional_indexes(db)
    await ensure_tpex_institutional_indexes(db)
    await ensure_margin_trading_indexes(db)
    await ensure_futures_oi_indexes(db)
    await ensure_futures_institutional_indexes(db)
    await ensure_taiex_exchange_indexes(db)
    await ensure_sector_flow_indexes(db)

    # 載入任務模組
    import app.scheduler.tasks  # noqa: F401
    from app.scheduler.tasks.twse_tasks import (
        twse_check_open,
        taiex_exchange_fetch,
        futures_institutional_fetch,
        twse_institutional_fetch,
        futures_oi_fetch,
        tpex_institutional_fetch,
        margin_trading_fetch,
        sector_flow_fetch,
    )

    # 依序執行（開盤狀態必須先跑，其他任務依賴它）
    tasks = [
        ("台股開盤狀態", twse_check_open),
        ("台股指數與匯率", taiex_exchange_fetch),
        ("期貨三大法人未平倉", futures_institutional_fetch),
        ("上市三大法人", twse_institutional_fetch),
        ("台指期未平倉", futures_oi_fetch),
        ("上櫃三大法人", tpex_institutional_fetch),
        ("融資融券餘額", margin_trading_fetch),
        ("類股資金流向", sector_flow_fetch),
    ]

    logger.info("=" * 50)
    logger.info("開始補足所有排程資料")
    logger.info("=" * 50)

    results = []
    for name, task_func in tasks:
        logger.info(f"\n--- {name} ---")
        try:
            summary = await task_func({})
            results.append((name, "✓", summary))
            logger.info(f"  完成: {summary}")
        except Exception as e:
            results.append((name, "✗", str(e)))
            logger.error(f"  失敗: {e}")

    # 總結
    logger.info("\n" + "=" * 50)
    logger.info("補足完成 — 結果總覽")
    logger.info("=" * 50)
    for name, status, detail in results:
        logger.info(f"  {status} {name}: {detail}")

    await close_redis()
    await close_mongodb()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="補足近期所有排程任務缺漏的資料")
    parser.add_argument("--days", type=int, default=None, help="回溯天數（預設使用 config 設定值）")
    args = parser.parse_args()
    asyncio.run(main(args.days))
