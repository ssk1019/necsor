"""
排程任務模組。

所有爬蟲 / 排程任務放在此目錄下。
新增任務只需：
1. 在此目錄建立新的 .py 檔
2. 使用 @register_task("task_type") 裝飾器註冊
3. 在 MongoDB schedule_jobs 集合中新增對應的排程設定

範例見 example_tasks.py
"""

# 匯入所有任務模組，觸發裝飾器註冊
from app.scheduler.tasks import example_tasks  # noqa: F401
from app.scheduler.tasks import twse_tasks     # noqa: F401

# 未來新增爬蟲時，在這裡加一行 import 即可：
# from app.scheduler.tasks import stock_crawler  # noqa: F401
# from app.scheduler.tasks import news_crawler   # noqa: F401
