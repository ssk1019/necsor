"""
時間相關共用工具。
"""

from datetime import datetime

import pytz

# 預設時區
TAIPEI_TZ = pytz.timezone("Asia/Taipei")


def now_taipei() -> datetime:
    """取得目前台北時間。"""
    return datetime.now(TAIPEI_TZ)


def now_log_prefix() -> str:
    """
    產生日誌前綴字串（台北時間）。

    格式: [YYYY-MM-DD HH:MM:SS]
    用於 fetch_log 等需要人類可讀時間戳的場景。
    """
    return f"[{now_taipei().strftime('%Y-%m-%d %H:%M:%S')}]"
