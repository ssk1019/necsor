---
inclusion: fileMatch
fileMatchPattern: "Backend/**"
---

# Backend Development Guide

## Directory Structure

```
Backend/
├── app/
│   ├── api/                  # HTTP 層
│   │   ├── deps.py           # 共用 FastAPI 依賴注入 (get_db, get_cache)
│   │   └── v1/
│   │       ├── router.py     # 聚合所有 v1 端點路由
│   │       └── endpoints/    # 每個資源一個檔案 (health.py, scheduler.py 等)
│   ├── core/                 # 跨模組基礎設施
│   │   ├── config.py         # 設定單例 (pydantic-settings)
│   │   ├── database.py       # MongoDB + Redis 連線管理
│   │   ├── logging.py        # loguru 設定
│   │   └── security.py       # JWT / 密碼雜湊
│   ├── middleware/            # 自訂 ASGI 中間件
│   ├── models/               # MongoDB 文件模型
│   │   ├── base.py           # TimestampMixin
│   │   └── scheduler.py      # 排程任務模型 (ScheduleJob, JobExecutionLog)
│   ├── schemas/              # Pydantic 請求/回應 Schema
│   │   ├── common.py         # ResponseBase[T], PaginatedResponse[T]
│   │   └── scheduler.py      # 排程 CRUD Schema
│   ├── scheduler/            # 排程引擎
│   │   ├── constants.py      # 集合名稱與預設值常數
│   │   ├── engine.py         # 排程主引擎 (SchedulerEngine)
│   │   ├── registry.py       # 任務註冊器 (@register_task 裝飾器)
│   │   ├── utils.py          # 共用工具（cron 計算等）
│   │   └── tasks/            # 排程任務實作
│   │       ├── __init__.py   # 匯入所有任務模組
│   │       └── example_tasks.py  # 範例任務
│   ├── services/             # 業務邏輯層
│   ├── utils/                # 共用工具
│   │   └── cache.py          # Redis 快取工具
│   └── main.py               # 應用程式入口 + 生命週期管理
├── tests/
├── .env / .env.example
└── requirements.txt
```

## Conventions

- **Adding a new resource:**
  1. Create model in `models/` (extend TimestampMixin if needed)
  2. Create schemas in `schemas/` (request + response)
  3. Create service in `services/` (business logic, DB queries)
  4. Create endpoint in `api/v1/endpoints/`
  5. Register router in `api/v1/router.py`

- **Database access:** Always use `Depends(get_db)` or `Depends(get_cache)` from `api/deps.py`. Never import database globals directly in endpoints.

- **Response format:** Wrap responses with `ResponseBase[T]` or `PaginatedResponse[T]` from `schemas/common.py`.

- **Environment variables:** Add new vars to both `.env` and `.env.example`, and add the field to `core/config.py` Settings class.

## Running

**Important:** Must `cd Backend` first. On Windows PowerShell, use `.\venv\Scripts\` prefix (not `Backend\venv\Scripts\` from root — PowerShell misinterprets it as a module import).

```powershell
# Activate venv (from Backend/)
.\venv\Scripts\Activate.ps1

# Start dev server (auto-reload)
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000

# Or if venv is activated:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
```

**Prerequisites:** Local MongoDB and Redis services must be running before startup.

## Key Dependencies

| Package | Purpose |
|---------|---------|
| fastapi 0.115.12 | Web framework |
| uvicorn 0.34.2 | ASGI server |
| motor 3.7.1 | Async MongoDB driver |
| beanie 1.29.0 | MongoDB ODM |
| redis 5.3.0 | Async Redis client (with hiredis) |
| pydantic-settings 2.9.1 | Config from env |
| python-jose 3.4.0 | JWT tokens |
| passlib 1.7.4 | Password hashing (bcrypt) |
| loguru 0.7.3 | Logging |
| croniter 5.0.1 | Cron 表達式解析（排程引擎） |

## 排程器

排程引擎在 FastAPI 啟動時自動載入，從 MongoDB `schedule_jobs` 集合讀取排程設定。

### 新增爬蟲任務步驟

1. 在 `scheduler/tasks/` 建立新的 `.py` 檔
2. 使用 `@register_task("task_type")` 裝飾器註冊
3. 在 `scheduler/tasks/__init__.py` 加入 import
4. 透過 API 或直接在 MongoDB 建立排程設定

### 任務函式規範

```python
@register_task("my_crawler")
async def my_crawler(params: dict) -> str:
    # params 來自 ScheduleJob.task_params
    # 回傳 str 作為執行結果摘要
    # 拋出例外表示失敗（會觸發重試）
    return "完成"
```

### 排程 API

- `GET    /api/v1/scheduler`              — 列出所有排程
- `GET    /api/v1/scheduler/task-types`   — 列出已註冊任務類型
- `GET    /api/v1/scheduler/{job_id}`     — 取得單一排程
- `POST   /api/v1/scheduler`             — 建立排程
- `PUT    /api/v1/scheduler/{job_id}`     — 更新排程
- `DELETE /api/v1/scheduler/{job_id}`     — 刪除排程
- `POST   /api/v1/scheduler/{job_id}/trigger` — 手動觸發
- `GET    /api/v1/scheduler/{job_id}/logs`    — 查詢執行紀錄

### MongoDB 集合

- `schedule_jobs` — 排程任務設定
- `job_execution_logs` — 執行紀錄
