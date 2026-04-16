"""
排程器共用工具函式。
抽出 engine 和 API 端點都需要的邏輯，避免重複。
"""

from datetime import datetime, timezone

import pytz
from croniter import croniter


def calc_next_run(cron_expression: str, tz: str = "Asia/Taipei") -> datetime:
    """
    根據 cron 表達式計算下次執行時間。

    Args:
        cron_expression: 標準 cron 表達式（分 時 日 月 週）
        tz: 時區名稱，預設 Asia/Taipei

    Returns:
        下次執行時間（UTC）
    """
    local_tz = pytz.timezone(tz)
    now_local = datetime.now(local_tz)
    cron = croniter(cron_expression, now_local)
    next_local = cron.get_next(datetime)
    if next_local.tzinfo is None:
        next_local = local_tz.localize(next_local)
    return next_local.astimezone(timezone.utc)
