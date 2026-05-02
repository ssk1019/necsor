---
inclusion: fileMatch
fileMatchPattern: "Frontend/**"
description: "前端目錄結構、開發慣例、圖表元件、深色模式、Nuxt 模組與套件"
---

# Frontend 開發指南

## 目錄結構

```
Frontend/
├── assets/scss/
│   ├── _variables.scss       # 設計變數（顏色、字型、斷點、圓角、陰影）
│   ├── _chart-card.scss      # 圖表卡片共用樣式（支援深色模式）
│   └── main.scss             # 全域樣式 + CSS 變數（淺色/深色兩組）
├── components/
│   ├── ui/                   # 通用 UI 元件
│   │   └── AppButton.vue
│   └── chart/                # 圖表元件（皆為 .client.vue，僅客戶端渲染）
│       ├── InstitutionalChart.client.vue      # 三大法人長條圖
│       ├── MarginChart.client.vue             # 融資融券曲線圖
│       ├── FuturesOIChart.client.vue          # 台指期混合圖
│       ├── FuturesInstitutionalChart.client.vue # 期貨三大法人長條圖（含 5 種商品 Tab）
│       └── TaiexExchangeChart.client.vue      # 台股加權指數 vs 匯率曲線圖
├── composables/
│   ├── useApi.ts             # 通用 API 封裝
│   ├── useMarketApi.ts       # 市場資料 API（三大法人、融資融券、台指期）
│   └── useChartTheme.ts      # 圖表深色模式配色
├── layouts/
│   └── default.vue           # 預設版面（導覽列 + 深色模式切換按鈕）
├── middleware/                # 路由中間件
├── pages/
│   ├── index.vue             # 首頁
│   └── market.vue            # 市場總覽（6 個圖表）
├── plugins/                  # Nuxt 插件
├── public/                   # 靜態資源
├── server/                   # Nitro 伺服器路由
├── stores/
│   └── app.ts                # Pinia 全域狀態
├── types/
│   └── index.ts              # 共用 TypeScript 型別
├── .env / .env.example
├── .nuxtrc                   # Nuxt 本地設定（telemetry 已關閉）
├── nuxt.config.ts            # Nuxt 設定
└── package.json
```

## 開發慣例

- **元件：** 通用 UI 放 `components/ui/`，功能元件放 `components/<feature>/`
- **圖表元件：** 使用 `.client.vue` 後綴（Chart.js 依賴 Canvas，無法 SSR）
- **圖表樣式：** 卡片樣式統一用 `@use "~/assets/scss/chart-card"`，配色用 `useChartTheme()` composable
- **Composables：** 放 `composables/`，Nuxt 自動匯入
- **頁面：** 檔案路由，`pages/about.vue` → `/about`
- **深色模式：** 用 CSS 變數（`var(--bg-card)` 等），定義在 `main.scss` 的 `:root` 和 `.dark`
- **API 呼叫：** 市場資料用 `useMarketApi()`，通用用 `useApi()`

## 深色模式

- 模組：`@nuxtjs/color-mode`
- 預設：深色（`preference: "dark"`）
- 切換按鈕：導覽列右側 ☀️/🌙
- 偏好自動存入 localStorage
- CSS 變數定義在 `main.scss`，`.dark` class 覆蓋淺色值

## 啟動方式

```bash
npm run dev          # http://localhost:3000
npm run build        # 正式建置
npm run preview      # 預覽正式建置
```

**注意：** Nuxt telemetry 已關閉（`.nuxtrc`）。若提示重新出現，執行 `npx nuxt telemetry disable`。

## Nuxt 模組

| 模組 | 用途 |
|------|------|
| @pinia/nuxt | 狀態管理 |
| @vueuse/nuxt | Vue 組合式工具 |
| @nuxt/eslint | 程式碼檢查 |
| @nuxtjs/color-mode | 深色/淺色模式 |

## 前端套件

| 套件 | 用途 |
|------|------|
| chart.js | 圖表繪製引擎 |
| vue-chartjs | Chart.js 的 Vue 封裝 |
| sass-embedded | SCSS 編譯 |
| ofetch | HTTP 客戶端 |

## 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| NUXT_PUBLIC_API_BASE | http://localhost:8000/api/v1 | 後端 API 基礎 URL |
