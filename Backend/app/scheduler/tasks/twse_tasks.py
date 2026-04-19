"""
台股相關排程任務。
"""

from datetime import date, timedelta

from loguru import logger

from app.core.config import get_settings
from app.core.database import get_database
from app.scheduler.registry import register_task
from app.services.twse_calendar import check_and_save_twse_open
from app.services.twse_institutional import check_and_save_institutional


@register_task("twse_check_open")
async def twse_check_open(params: dict) -> str:
    """
    檢查台股當日是否開盤，並回溯補抓近 N 日缺漏的紀錄。

    回溯天數由 Settings.TWSE_OPEN_CHECK_BACKFILL_DAYS 控制。
    每筆檢查皆為冪等：已抓取過的日期會自動跳過。
    """
    settings = get_settings()
    db = get_database()
    today = date.today()
    backfill_days = settings.TWSE_OPEN_CHECK_BACKFILL_DAYS

    results = []
    for i in range(backfill_days - 1, -1, -1):
        target = today - timedelta(days=i)
        result = await check_and_save_twse_open(db, target)
        results.append(result)

    fetched = [r for r in results if not r["skipped"]]
    skipped = [r for r in results if r["skipped"]]

    summary_parts = []
    if fetched:
        dates_str = ", ".join(r["date"] for r in fetched)
        summary_parts.append(f"新抓取 {len(fetched)} 筆: {dates_str}")
    if skipped:
        summary_parts.append(f"跳過 {len(skipped)} 筆（已存在）")

    summary = "；".join(summary_parts) if summary_parts else "無需處理"
    logger.info(f"台股開盤檢查完成 — {summary}")
    return summary


@register_task("twse_institutional_fetch")
async def twse_institutional_fetch(params: dict) -> str:
    """
    抓取三大法人買賣金額統計表（上市），並回溯補抓近 N 日缺漏。

    執行邏輯：
    1. 從今天往前 N 日，逐日檢查
    2. 先確認該日是否有開盤（twse_is_open = True）
    3. 休市日跳過，已抓取過的跳過
    4. 有開盤但無資料的才抓取

    回溯天數由 Settings.TWSE_INSTITUTIONAL_BACKFILL_DAYS 控制。
    """
    settings = get_settings()
    db = get_database()
    today = date.today()
    backfill_days = settings.TWSE_INSTITUTIONAL_BACKFILL_DAYS

    fetched_dates = []
    skipped_count = 0
    closed_count = 0
    error_dates = []

    for i in range(backfill_days - 1, -1, -1):
        target = today - timedelta(days=i)
        try:
            result = await check_and_save_institutional(db, target)
            if result["status"] == "fetched":
                fetched_dates.append(result["date"])
            elif result["status"] == "closed":
                closed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            error_dates.append(target.strftime("%Y-%m-%d"))
            logger.error(f"{target} 三大法人抓取失敗: {e}")

    summary_parts = []
    if fetched_dates:
        summary_parts.append(f"新抓取 {len(fetched_dates)} 筆: {', '.join(fetched_dates)}")
    if skipped_count:
        summary_parts.append(f"跳過 {skipped_count} 筆（已存在或無開盤狀態）")
    if closed_count:
        summary_parts.append(f"休市 {closed_count} 日")
    if error_dates:
        summary_parts.append(f"失敗 {len(error_dates)} 筆: {', '.join(error_dates)}")

    summary = "；".join(summary_parts) if summary_parts else "無需處理"
    logger.info(f"三大法人抓取完成 — {summary}")
    return summary


@register_task("tpex_institutional_fetch")
async def tpex_institutional_fetch(params: dict) -> str:
    """
    抓取上櫃三大法人買賣金額統計表，並回溯補抓近 N 日缺漏。

    執行邏輯：
    1. 從今天往前 N 日，逐日檢查
    2. 先確認該日是否有開盤（twse_is_open = True）
    3. 休市日跳過，已抓取過的跳過
    4. 有開盤但無資料的才抓取

    回溯天數由 Settings.TPEX_INSTITUTIONAL_BACKFILL_DAYS 控制。
    """
    from app.services.tpex_institutional import check_and_save_tpex_institutional

    settings = get_settings()
    db = get_database()
    today = date.today()
    backfill_days = settings.TPEX_INSTITUTIONAL_BACKFILL_DAYS

    fetched_dates = []
    skipped_count = 0
    closed_count = 0
    error_dates = []

    for i in range(backfill_days - 1, -1, -1):
        target = today - timedelta(days=i)
        try:
            result = await check_and_save_tpex_institutional(db, target)
            if result["status"] == "fetched":
                fetched_dates.append(result["date"])
            elif result["status"] == "closed":
                closed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            error_dates.append(target.strftime("%Y-%m-%d"))
            logger.error(f"{target} 上櫃三大法人抓取失敗: {e}")

    summary_parts = []
    if fetched_dates:
        summary_parts.append(f"新抓取 {len(fetched_dates)} 筆: {', '.join(fetched_dates)}")
    if skipped_count:
        summary_parts.append(f"跳過 {skipped_count} 筆（已存在或無開盤狀態）")
    if closed_count:
        summary_parts.append(f"休市 {closed_count} 日")
    if error_dates:
        summary_parts.append(f"失敗 {len(error_dates)} 筆: {', '.join(error_dates)}")

    summary = "；".join(summary_parts) if summary_parts else "無需處理"
    logger.info(f"上櫃三大法人抓取完成 — {summary}")
    return summary


@register_task("margin_trading_fetch")
async def margin_trading_fetch(params: dict) -> str:
    """
    抓取融資融券餘額統計，並回溯補抓近 N 日缺漏。

    執行邏輯：
    1. 從今天往前 N 日，逐日檢查
    2. 先確認該日是否有開盤（twse_is_open = True）
    3. 休市日跳過，已抓取過的跳過
    4. 有開盤但無資料的才抓取

    回溯天數由 Settings.MARGIN_TRADING_BACKFILL_DAYS 控制。
    """
    from app.services.margin_trading import check_and_save_margin

    settings = get_settings()
    db = get_database()
    today = date.today()
    backfill_days = settings.MARGIN_TRADING_BACKFILL_DAYS

    fetched_dates = []
    skipped_count = 0
    closed_count = 0
    error_dates = []

    for i in range(backfill_days - 1, -1, -1):
        target = today - timedelta(days=i)
        try:
            result = await check_and_save_margin(db, target)
            if result["status"] == "fetched":
                fetched_dates.append(result["date"])
            elif result["status"] == "closed":
                closed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            error_dates.append(target.strftime("%Y-%m-%d"))
            logger.error(f"{target} 融資融券抓取失敗: {e}")

    summary_parts = []
    if fetched_dates:
        summary_parts.append(f"新抓取 {len(fetched_dates)} 筆: {', '.join(fetched_dates)}")
    if skipped_count:
        summary_parts.append(f"跳過 {skipped_count} 筆（已存在或無開盤狀態）")
    if closed_count:
        summary_parts.append(f"休市 {closed_count} 日")
    if error_dates:
        summary_parts.append(f"失敗 {len(error_dates)} 筆: {', '.join(error_dates)}")

    summary = "；".join(summary_parts) if summary_parts else "無需處理"
    logger.info(f"融資融券抓取完成 — {summary}")
    return summary


@register_task("futures_oi_fetch")
async def futures_oi_fetch(params: dict) -> str:
    """
    抓取台指期未平倉口數，並回溯補抓近 N 日缺漏。

    資料來源：FinMind API（TaiwanFuturesDaily）。
    回溯天數由 Settings.FUTURES_OI_BACKFILL_DAYS 控制。
    """
    from app.services.futures_oi import check_and_save_futures_oi

    settings = get_settings()
    db = get_database()
    today = date.today()
    backfill_days = settings.FUTURES_OI_BACKFILL_DAYS

    fetched_dates = []
    skipped_count = 0
    closed_count = 0
    error_dates = []

    for i in range(backfill_days - 1, -1, -1):
        target = today - timedelta(days=i)
        try:
            result = await check_and_save_futures_oi(db, target)
            if result["status"] == "fetched":
                fetched_dates.append(result["date"])
            elif result["status"] == "closed":
                closed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            error_dates.append(target.strftime("%Y-%m-%d"))
            logger.error(f"{target} 台指期抓取失敗: {e}")

    summary_parts = []
    if fetched_dates:
        summary_parts.append(f"新抓取 {len(fetched_dates)} 筆: {', '.join(fetched_dates)}")
    if skipped_count:
        summary_parts.append(f"跳過 {skipped_count} 筆（已存在或無開盤狀態）")
    if closed_count:
        summary_parts.append(f"休市 {closed_count} 日")
    if error_dates:
        summary_parts.append(f"失敗 {len(error_dates)} 筆: {', '.join(error_dates)}")

    summary = "；".join(summary_parts) if summary_parts else "無需處理"
    logger.info(f"台指期抓取完成 — {summary}")
    return summary


@register_task("futures_institutional_fetch")
async def futures_institutional_fetch(params: dict) -> str:
    """
    抓取期貨三大法人未平倉餘額，並回溯補抓近 N 日缺漏。

    資料來源：FinMind API（TaiwanFuturesInstitutionalInvestors）。
    回溯天數由 Settings.FUTURES_INSTITUTIONAL_BACKFILL_DAYS 控制。
    """
    from app.services.futures_institutional import check_and_save_futures_institutional

    settings = get_settings()
    db = get_database()
    today = date.today()
    backfill_days = settings.FUTURES_INSTITUTIONAL_BACKFILL_DAYS

    fetched_dates = []
    skipped_count = 0
    closed_count = 0
    error_dates = []

    for i in range(backfill_days - 1, -1, -1):
        target = today - timedelta(days=i)
        try:
            result = await check_and_save_futures_institutional(db, target)
            if result["status"] == "fetched":
                fetched_dates.append(result["date"])
            elif result["status"] == "closed":
                closed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            error_dates.append(target.strftime("%Y-%m-%d"))
            logger.error(f"{target} 期貨三大法人抓取失敗: {e}")

    summary_parts = []
    if fetched_dates:
        summary_parts.append(f"新抓取 {len(fetched_dates)} 筆: {', '.join(fetched_dates)}")
    if skipped_count:
        summary_parts.append(f"跳過 {skipped_count} 筆（已存在或無開盤狀態）")
    if closed_count:
        summary_parts.append(f"休市 {closed_count} 日")
    if error_dates:
        summary_parts.append(f"失敗 {len(error_dates)} 筆: {', '.join(error_dates)}")

    summary = "；".join(summary_parts) if summary_parts else "無需處理"
    logger.info(f"期貨三大法人抓取完成 — {summary}")
    return summary
