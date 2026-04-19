---
inclusion: fileMatch
fileMatchPattern: "Backend/**"
---

# Backend 開發指南

## 目錄結構

```
Backend/
├── app/
│   ├── api/                  # HTTP 層
│   │   ├── deps.py           # 共用 FastAPI 依賴注入 (get_db, get_cache)
│   │   └── v1/
│   │       ├── router.py     # 聚合所有 v1 端點路由
│   │       └── endpoints/    # 每個資源一個檔案
│   │           ├── health.py
│   │           └── scheduler.py
│   ├── core/                 # 跨模組基礎設施
│   │   ├── config.py         # 集中設定（pydantic-settings，含業務設定）
│   │   ├── database.py       # MongoDB + Redis 連線管理
│   │   ├── logging.py        # loguru 設定
│   │   └── security.py       # JWT / 密碼雜湊
│   ├── middleware/            # 自訂 ASGI 中間件
│   ├── models/               # MongoDB 文件模型
│   │   ├── base.py           # TimestampMixin
│   │   ├── scheduler.py      # 排程任務模型
│   │   ├── daily_market.py   # 每日抓取狀態總表模型
│   │   ├── twse_institutional.py  # 上市三大法人資料模型
│   │   └── tpex_institutional.py  # 上櫃三大法人資料模型
│   ├── schemas/              # Pydantic 請求/回應 Schema
│   │   ├── common.py         # ResponseBase[T], PaginatedResponse[T]
│   │   └── scheduler.py      # 排程 CRUD Schema
│   ├── scheduler/            # 排程引擎
│   │   ├── constants.py      # 集合名稱與預設值常數
│   │   ├── engine.py         # 排程主引擎 (SchedulerEngine)
│   │   ├── registry.py       # 任務註冊器 (@register_task)
│   │   ├── utils.py          # 共用工具（cron 計算等）
│   │   └── tasks/            # 排程任務實作
│   │       ├── __init__.py   # 匯入所有任務模組
│   │       ├── example_tasks.py
│   │       └── twse_tasks.py # 台股相關排程任務
│   ├── services/             # 業務邏輯層
│   │   ├── twse_calendar.py       # 台股開休市判斷
│   │   ├── twse_institutional.py  # 上市三大法人抓取
│   │   └── tpex_institutional.py  # 上櫃三大法人抓取
│   ├── utils/                # 共用工具
│   │   ├── cache.py          # Redis 快取工具
│   │   └── time.py           # 時間工具（now_taipei, now_log_prefix）
│   └── main.py               # 應用程式入口 + 生命週期管理
├── tests/
├── .env / .env.example
└── requirements.txt
```

## 開發慣例

- **新增資源步驟：**
  1. 在 `models/` 建立資料模型
  2. 在 `schemas/` 建立請求/回應 Schema
  3. 在 `services/` 建立業務邏輯
  4. 在 `api/v1/endpoints/` 建立端點
  5. 在 `api/v1/router.py` 註冊路由

- **新增每日抓取功能步驟：**
  1. 在 `models/` 建立獨立資料表模型（date 唯一降冪索引）
  2. 在 `daily_market.py` 加入布林旗標欄位（None/True/False）
  3. 在 `services/` 建立抓取邏輯（含冪等檢查、fetch_log 記錄）
  4. 在 `scheduler/tasks/twse_tasks.py` 加入排程任務（含回溯補抓）
  5. 在 `main.py` 加入索引建立
  6. 在 `config.py` 加入回溯天數設定
  7. 透過 API 建立排程設定

- **資料庫存取：** 一律透過 `Depends(get_db)` 或 `Depends(get_cache)`，不直接 import 全域變數。

- **回應格式：** 使用 `ResponseBase[T]` 或 `PaginatedResponse[T]`。

- **環境變數：** 新增時同步更新 `.env`、`.env.example`、`config.py`。

- **業務設定集中管理：** 所有業務設定放在 `core/config.py` 的 `Settings` 類別中 `# === 業務設定 ===` 區塊。

- **時間處理：** fetch_log 使用台北時間（`utils/time.py` 的 `now_log_prefix()`），MongoDB 時間戳使用 UTC。

## 啟動方式

**必須先 `cd Backend`。** Windows PowerShell 用 `.\venv\Scripts\` 前綴。

```powershell
.\venv\Scripts\Activate.ps1
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

**前置條件：** 本地 MongoDB 和 Redis 服務必須先啟動。

## 主要套件

| 套件 | 用途 |
|------|------|
| fastapi 0.115.12 | Web 框架 |
| uvicorn 0.34.2 | ASGI 伺服器 |
| motor 3.7.1 | 非同步 MongoDB 驅動 |
| redis 5.3.0 | 非同步 Redis（含 hiredis） |
| croniter 5.0.1 | Cron 表達式解析 |
| httpx 0.28.1 | 非同步 HTTP 客戶端 |
| pydantic-settings 2.9.1 | 環境變數設定 |
| loguru 0.7.3 | 日誌 |

## 排程器系統

排程引擎在 FastAPI 啟動時自動載入，從 MongoDB `schedule_jobs` 讀取設定。

### 新增排程任務

1. 在 `scheduler/tasks/` 建立或編輯 `.py` 檔
2. 使用 `@register_task("task_type")` 裝飾器
3. 在 `scheduler/tasks/__init__.py` 加入 import
4. 透過 API 建立排程設定

### 任務函式規範

```python
@register_task("my_task")
async def my_task(params: dict) -> str:
    # params 來自 ScheduleJob.task_params
    # 回傳 str 作為結果摘要
    # 拋出例外 → 觸發重試
    return "完成"
```

### 排程 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/scheduler` | 列出所有排程 |
| GET | `/api/v1/scheduler/task-types` | 已註冊任務類型 |
| GET | `/api/v1/scheduler/{job_id}` | 單一排程詳情 |
| POST | `/api/v1/scheduler` | 建立排程 |
| PUT | `/api/v1/scheduler/{job_id}` | 更新排程 |
| DELETE | `/api/v1/scheduler/{job_id}` | 刪除排程 |
| POST | `/api/v1/scheduler/{job_id}/trigger` | 手動觸發 |
| GET | `/api/v1/scheduler/{job_id}/logs` | 執行紀錄 |

## MongoDB 資料表

| 集合 | 用途 | 主鍵 |
|------|------|------|
| `schedule_jobs` | 排程任務設定 | job_id |
| `job_execution_logs` | 排程執行紀錄 | — |
| `daily_market_fetch` | 每日抓取狀態總表（旗標 + fetch_log） | date（唯一降冪） |
| `twse_institutional` | 上市三大法人買賣金額數據 | date（唯一降冪） |
| `tpex_institutional` | 上櫃三大法人買賣金額數據 | date（唯一降冪） |

### daily_market_fetch 欄位說明

此表為所有每日抓取功能的狀態總表，以日期為主鍵。

| 欄位 | 型別 | 說明 |
|------|------|------|
| date | str | 日期 YYYY-MM-DD（唯一主鍵） |
| twse_is_open | bool/None | 台股當日是否開盤 |
| twse_institutional | bool/None | 上市三大法人是否已抓取 |
| tpex_institutional | bool/None | 上櫃三大法人是否已抓取 |
| fetch_log | str | 抓取紀錄日誌（每行格式: `[YYYY-MM-DD HH:MM:SS] 訊息`） |
| created_at / updated_at | datetime | 時間戳（UTC） |

新增抓取功能時，在此表加一個布林旗標欄位，實際數據存獨立表。

## 目前排程任務

| job_id | task_type | Cron | 說明 |
|--------|-----------|------|------|
| twse_daily_open_check | twse_check_open | `0 7 * * *` | 每日 07:00 檢查台股開盤狀態 |
| twse_institutional_daily | twse_institutional_fetch | `10 16 * * *` | 每日 16:10 上市三大法人 |
| tpex_institutional_daily | tpex_institutional_fetch | `20 16 * * *` | 每日 16:20 上櫃三大法人 |

所有抓取任務都有回溯補抓機制，天數由 `config.py` 的業務設定控制。

## 業務設定（config.py）

| 設定 | 預設值 | 說明 |
|------|--------|------|
| TWSE_OPEN_CHECK_BACKFILL_DAYS | 5 | 台股開盤檢查回溯天數 |
| TWSE_INSTITUTIONAL_BACKFILL_DAYS | 5 | 上市三大法人回溯天數 |
| TPEX_INSTITUTIONAL_BACKFILL_DAYS | 5 | 上櫃三大法人回溯天數 |

## 外部 API 資料來源

| 來源 | API | 用途 |
|------|-----|------|
| 證交所 (TWSE) | `twse.com.tw/rwd/zh/holidaySchedule/holidaySchedule` | 開休市日期 |
| 證交所 (TWSE) | `twse.com.tw/rwd/zh/fund/BFI82U` | 上市三大法人買賣金額 |
| 櫃買中心 (TPEx) | `tpex.org.tw/web/stock/3insti/3insti_summary/3itrdsum_result.php` | 上櫃三大法人買賣金額 |

注意：櫃買中心 API 使用民國年日期格式（如 115/04/17）。
