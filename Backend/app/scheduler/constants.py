"""
排程器常數定義。
集中管理集合名稱與預設值，避免散落各處。
"""

# MongoDB 集合名稱
JOBS_COLLECTION = "schedule_jobs"
LOGS_COLLECTION = "job_execution_logs"

# 排程引擎檢查間隔（秒）
CHECK_INTERVAL = 15
