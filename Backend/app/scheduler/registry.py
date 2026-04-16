"""
任務註冊器。

使用裝飾器模式，讓新增爬蟲任務變得極為簡單：

    from app.scheduler.registry import register_task

    @register_task("crawler_stock")
    async def crawl_stock(params: dict) -> str:
        # ... 爬蟲邏輯 ...
        return "抓取了 100 筆資料"

任務函式規範：
- 必須是 async 函式
- 接收一個 dict 參數（來自 ScheduleJob.task_params）
- 回傳 str 作為執行結果摘要
- 拋出例外表示執行失敗
"""

from typing import Callable, Awaitable, Dict
from loguru import logger

# 全域任務註冊表：task_type -> async function
_task_registry: Dict[str, Callable[[dict], Awaitable[str]]] = {}


def register_task(task_type: str):
    """
    任務註冊裝飾器。

    用法：
        @register_task("my_crawler")
        async def my_crawler(params: dict) -> str:
            ...
    """
    def decorator(func: Callable[[dict], Awaitable[str]]):
        if task_type in _task_registry:
            logger.warning(f"任務類型 '{task_type}' 已被註冊，將被覆蓋")
        _task_registry[task_type] = func
        logger.debug(f"已註冊任務類型: {task_type} -> {func.__name__}")
        return func
    return decorator


def get_task(task_type: str) -> Callable[[dict], Awaitable[str]] | None:
    """根據 task_type 取得對應的任務函式。"""
    return _task_registry.get(task_type)


def get_all_task_types() -> list[str]:
    """取得所有已註冊的任務類型。"""
    return list(_task_registry.keys())
