---
inclusion: auto
---

# 專案概覽 — Necsor

高吞吐、強併發、快速回應的全端 Web 應用程式。

## 技術棧

### Backend (`Backend/`)
- **語言：** Python 3.12
- **框架：** FastAPI（非同步高效能）
- **資料庫：** MongoDB（本地服務，motor 非同步驅動）
- **快取：** Redis（本地服務，redis-py 非同步 + hiredis）
- **設定：** pydantic-settings + python-dotenv
- **排程：** 自建排程引擎（croniter + MongoDB 設定）
- **HTTP 客戶端：** httpx（非同步，用於抓取外部 API）
- **日誌：** loguru
- **虛擬環境：** `Backend/venv/`（Python 3.12）

### Frontend (`Frontend/`)
- **執行環境：** Node.js 22 LTS（nvm 管理）
- **框架：** Nuxt 3（Vue 3，支援 SSR）
- **狀態管理：** Pinia
- **工具庫：** VueUse
- **樣式：** SCSS（sass-embedded）
- **套件管理：** npm

## Git 倉庫

- **GitHub：** https://github.com/ssk1019/necsor.git
- **Remote：** origin
- **主分支：** main
- 當使用者要求 push 時，直接執行 `git push origin main`（或推送至對應分支）

## 架構原則

1. **關注點分離** — API 路由、業務邏輯（services）、資料模型、Schema 各自獨立
2. **全面非同步** — 前後端皆為非同步架構
3. **設定集中管理** — 後端 `core/config.py`，前端 `nuxt.config.ts`，皆從 `.env` 載入
4. **API 版本化** — 後端路由前綴 `/api/v1`
5. **依賴注入** — FastAPI `Depends()` 模式
6. **冪等抓取** — 所有資料抓取任務皆為冪等設計，已抓取的自動跳過
7. **回溯補抓** — 抓取任務會自動檢查近 N 日缺漏並補抓

## 目前功能

### 排程系統
- 自建排程引擎，設定存於 MongoDB，支援 cron 表達式
- 重試策略（次數、間隔、指數退避）
- Misfire 策略（補執行 / 跳過）
- 管理 API（CRUD + 手動觸發 + 紀錄查詢）

### 每日資料抓取
- 台股開盤狀態檢查（證交所 API）
- 上市三大法人買賣金額（證交所 BFI82U API）
- 上櫃三大法人買賣金額（櫃買中心 3itrdsum API）
- 所有抓取狀態統一記錄在 `daily_market_fetch` 總表
- 實際數據存於各自獨立資料表
