"""
範例排程任務。

展示如何使用 @register_task 裝飾器註冊新任務。
可作為未來新增爬蟲的模板。
"""

import asyncio

from loguru import logger

from app.scheduler.registry import register_task


@register_task("example_hello")
async def example_hello(params: dict) -> str:
    """
    範例任務：印出問候訊息。

    params 範例：{"name": "Necsor"}
    """
    name = params.get("name", "World")
    logger.info(f"範例任務執行中: Hello, {name}!")
    await asyncio.sleep(1)  # 模擬耗時操作
    return f"已問候 {name}"


@register_task("example_fail")
async def example_fail(params: dict) -> str:
    """
    範例任務：故意失敗（用於測試重試機制）。
    """
    raise RuntimeError("這是一個故意的錯誤，用於測試重試機制")
