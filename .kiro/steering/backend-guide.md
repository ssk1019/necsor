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
│   │   ├── deps.py           # 共用依賴注入 (get_db, get_cache)
│   │   └── v1/
│   │       ├── router.py     # 聚合所有 v1 端點路由
│   │       └── endpoints/
│   │           ├── health.py       # 健康檢查
│   │           ├── scheduler.py    # 排程管理 CRUD
│   │           └── market_data.py  # 市場資料查詢（供前端圖表）
│   ├── core/                 # 跨模組基礎設施
│   │   ├── config.py         # 集中設定（pydantic-settings，含業務設定）
│   │   ├── database.py       # MongoDB + Redis 連線管理
│   │   ├── logging.py        # loguru 設定
│   │   └── security.py       # JWT / 密碼雜湊
│   ├── middleware/            # 自訂 ASGI 中間件
│   ├── models/               # MongoDB 文件模型
│   │   ├── base.py                  # TimestampMixin
│   │   ├── scheduler.py             # 排程任務模型
│   │   ├── daily_market.py          # 每日抓取狀態總表
│   │   ├── twse_institutional.py    # 上市三大法人
│   │   ├── tpex_institutional.py    # 上櫃三大法人
│   │   ├── margin_trading.py        # 融資融券餘額
│   │   ├── futures_oi.py            # 台指期未平倉
│   │   └── futures_institutional.py # 期貨三大法人未平倉
│   ├── schemas/              # Pydantic 請求/回應 Schema
│   │   ├── common.py         # ResponseBase[T], PaginatedResponse[T]
│   │   └── scheduler.py      # 排程 CRUD Schema
│   ├── scheduler/            # 排程引擎
│   │   ├── constants.py      # 集合名稱與預設值常數
│   │   ├── engine.py         # 排程主引擎
│   │   ├── registry.py       # 任務註冊器 (@register_task)
│   │   ├── utils.py          # 共用工具（cron 計算等）
│   │   └── tasks/
│   │       ├── __init__.py        # 匯入所有任務模組
│   │       ├── example_tasks.py   # 範例任務
│   │       └── twse_tasks.py      # 台股相關排程任務（全部）
│   ├── services/             # 業務邏輯層
│   │   ├── twse_calendar.py          # 台股開休市判斷
│   │   ├── twse_institutional.py     # 上市三大法人抓取
│   │   ├── tpex_institutional.py     # 上櫃三大法人抓取
│   │   ├── margin_trading.py         # 融資融券餘額抓取
│   │   ├── futures_oi.py             # 台指期未平倉抓取
│   │   └── futures_institutional.py  # 期貨三大法人未平倉抓取
│   ├── utils/
│   │   ├── cache.py          # Redis 快取工具
│   │   └── time.py           # 時間工具（now_taipei, now_log_prefix）
│   └── main.py               # 應用程式入口 + 生命週期管理
├── tests/
├── .env / .env.example
└── requirements.txt
```

## 開發慣例

- **新增每日抓取功能步驟：**
  1. 在 `models/` 建立獨立資料表模型（date 唯一降冪索引）
  2. 在 `models/daily_market.py` 加入布林旗標欄位（None/True/False）
  3. 在 `services/` 建立抓取邏輯（含冪等檢查、fetch_log 記錄）
  4. 在 `scheduler/tasks/twse_tasks.py` 加入排程任務（含回溯補抓）
  5. 在 `main.py` 加入 `ensure_xxx_indexes` 呼叫
  6. 在 `config.py` 加入回溯天數設定，同步更新 `.env` 和 `.env.example`
  7. 用 Python 腳本建立排程設定（避免 PowerShell 中文編碼問題）

- **資料庫存取：** 一律透過 `Depends(get_db)` 或 `Depends(get_cache)`
- **環境變數：** 新增時同步更新 `.env`、`.env.example`、`config.py`
- **業務設定：** 集中在 `core/config.py` 的 `# === 業務設定 ===` 區塊
- **時間處理：** fetch_log 用台北時間（`now_log_prefix()`），MongoDB 時間戳用 UTC
- **建立排程：** 用 Python 腳本直接寫入 MongoDB，不用 PowerShell（避免中文亂碼）

## 啟動方式

**必須先 `cd Backend`。** Windows PowerShell 用 `.\venv\Scripts\` 前綴。

```powershell
.\venv\Scripts\Activate.ps1
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

**前置條件：** 本地 MongoDB 和 Redis 服務必須先啟動。

## MongoDB 資料表

| 集合 | 用途 | 主鍵 |
|------|------|------|
| `schedule_jobs` | 排程任務設定 | job_id |
| `job_execution_logs` | 排程執行紀錄 | — |
| `daily_market_fetch` | 每日抓取狀態總表（旗標 + fetch_log） | date（唯一降冪） |
| `twse_institutional` | 上市三大法人買賣金額 | date（唯一降冪） |
| `tpex_institutional` | 上櫃三大法人買賣金額 | date（唯一降冪） |
| `margin_trading` | 融資融券餘額 | date（唯一降冪） |
| `futures_open_interest` | 台指期各合約未平倉口數 | date（唯一降冪） |
| `futures_institutional` | 期貨三大法人未平倉餘額 | date（唯一降冪） |

### daily_market_fetch 欄位

| 欄位 | 型別 | 說明 |
|------|------|------|
| date | str | 日期 YYYY-MM-DD（唯一主鍵） |
| twse_is_open | bool/None | 台股當日是否開盤 |
| twse_institutional | bool/None | 上市三大法人是否已抓取 |
| tpex_institutional | bool/None | 上櫃三大法人是否已抓取 |
| margin_trading | bool/None | 融資融券是否已抓取 |
| futures_oi | bool/None | 台指期未平倉是否已抓取 |
| futures_institutional | bool/None | 期貨三大法人是否已抓取 |
| fetch_log | str | 抓取紀錄（每行 `[YYYY-MM-DD HH:MM:SS] 訊息`） |

## 排程任務

| job_id | task_type | Cron | 說明 |
|--------|-----------|------|------|
| twse_daily_open_check | twse_check_open | `0 7 * * *` | 每日 07:00 開盤狀態 |
| futures_institutional_daily | futures_institutional_fetch | `50 15 * * *` | 每日 15:50 期貨三大法人 |
| twse_institutional_daily | twse_institutional_fetch | `10 16 * * *` | 每日 16:10 上市三大法人 |
| futures_oi_daily | futures_oi_fetch | `10 16 * * *` | 每日 16:10 台指期未平倉 |
| tpex_institutional_daily | tpex_institutional_fetch | `20 16 * * *` | 每日 16:20 上櫃三大法人 |
| margin_trading_daily | margin_trading_fetch | `10 21 * * *` | 每日 21:10 融資融券餘額 |

## 業務設定（config.py）

| 設定 | 預設值 | 說明 |
|------|--------|------|
| TWSE_OPEN_CHECK_BACKFILL_DAYS | 5 | 台股開盤檢查回溯天數 |
| TWSE_INSTITUTIONAL_BACKFILL_DAYS | 5 | 上市三大法人回溯天數 |
| TPEX_INSTITUTIONAL_BACKFILL_DAYS | 5 | 上櫃三大法人回溯天數 |
| MARGIN_TRADING_BACKFILL_DAYS | 5 | 融資融券回溯天數 |
| FUTURES_OI_BACKFILL_DAYS | 5 | 台指期未平倉回溯天數 |
| FUTURES_INSTITUTIONAL_BACKFILL_DAYS | 5 | 期貨三大法人回溯天數 |
| CHART_DEFAULT_DAYS | 30 | 圖表預設顯示天數 |
| FINMIND_API_TOKEN | — | FinMind API 金鑰（存於 .env） |

## 市場資料 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/market/institutional/twse?days=30` | 上市三大法人歷史 |
| GET | `/api/v1/market/institutional/tpex?days=30` | 上櫃三大法人歷史 |
| GET | `/api/v1/market/margin?days=30` | 融資融券餘額歷史 |
| GET | `/api/v1/market/futures-oi?days=30` | 台指期未平倉歷史 |
| GET | `/api/v1/market/futures-institutional?days=30` | 期貨三大法人歷史 |

## 外部 API 資料來源

| 來源 | API | 用途 |
|------|-----|------|
| 證交所 (TWSE) | `twse.com.tw/rwd/zh/holidaySchedule/holidaySchedule` | 開休市日期 |
| 證交所 (TWSE) | `twse.com.tw/rwd/zh/fund/BFI82U` | 上市三大法人買賣金額 |
| 證交所 (TWSE) | `twse.com.tw/rwd/zh/marginTrading/MI_MARGN` | 融資融券餘額 |
| 櫃買中心 (TPEx) | `tpex.org.tw/.../3itrdsum_result.php` | 上櫃三大法人買賣金額 |
| FinMind | `api.finmindtrade.com/api/v4/data` (TaiwanFuturesDaily) | 台指期未平倉 |
| FinMind | `api.finmindtrade.com/api/v4/data` (TaiwanFuturesInstitutionalInvestors) | 期貨三大法人 |

注意：櫃買中心 API 使用民國年日期格式（如 115/04/17）。FinMind 需要 API Token。
