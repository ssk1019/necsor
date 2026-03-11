# 高效能 Web 後台儀表板

本專案包含一個基於 Python FastAPI 的高效能後端，以及一個可擴充的 React Next.js 前端。專案設計旨在使用 MongoDB 和 Redis 來處理高流量請求。

## 專案結構

- **Backend/**: Python 3 + FastAPI + Motor (異步 MongoDB) + Redis
- **Frontend/**: React + Next.js (Node.js v20)
- **ecosystem.config.js**: 用於生產環境部署的 PM2 設定檔

---

## 先決條件

- **資料庫**: MongoDB (預設: `127.0.0.1:27017`)
- **快取**: Redis (預設: `127.0.0.1:6379`)
- **執行環境**:
  - Python 3.10+
  - Node.js v20 (透過 NVM 管理)
  - PM2 (生產環境全域安裝: `npm install -g pm2`)

---

## 1. 本地開發 (除錯模式)

### 後端 (Backend)
1. 進入 `Backend/` 目錄：
   ```bash
   cd Backend
   ```
2. 建立並啟用虛擬環境：
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```
3. 安裝相依套件：
   ```bash
   pip install -r requirements.txt
   ```
4. 啟動伺服器 (熱重載模式)：
   ```bash
   uvicorn main:app --reload
   ```
   *API 文件位於: http://127.0.0.1:8000/docs*

### 前端 (Frontend)
1. 進入 `Frontend/` 目錄：
   ```bash
   cd Frontend
   ```
2. 使用正確的 Node 版本：
   ```bash
   nvm use
   # 若未安裝: nvm install 20
   ```
3. 安裝相依套件：
   ```bash
   npm install
   ```
4. 啟動開發伺服器：
   ```bash
   npm run dev
   ```
   *網頁介面位於: http://localhost:3000*

---

## 2. 生產環境部署 (伺服器)

為了處理高併發並確保穩定性，建議使用 **PM2** 來管理進程，並使用 **Nginx** 作為反向代理。

### 步驟 1: 環境設定
1. 全域安裝 **PM2**：
   ```bash
   npm install -g pm2
   ```
2. **後端設定**：
   ```bash
   cd Backend
   python -m venv venv
   source venv/bin/activate  # 或 Windows 對應指令
   pip install -r requirements.txt
   # 確保已安裝 gunicorn
   ```
3. **前端建置 (Build)**：
   ```bash
   cd Frontend
   nvm use
   npm install
   npm run build
   # 此步驟會產生優化過的 .next/ 資料夾
   ```

### 步驟 2: 使用 PM2 啟動服務
回到專案根目錄並執行：
```bash
pm2 start ecosystem.config.js
```
此指令將啟動：
- **後端**: 使用 Gunicorn 搭配 Uvicorn worker (Port 8000)
- **前端**: Next.js 生產伺服器 (Port 3000)

### 步驟 3: 管理指令
- 查看狀態: `pm2 status`
- 監控日誌: `pm2 logs`
- 重啟所有服務: `pm2 restart all`
- 停止所有服務: `pm2 stop all`

---

## 3. Nginx 設定 (反向代理)

為了處理高流量並使用 Port 80/443，請設定 Nginx：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端 (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 後端 API (FastAPI)
    location /api/ {
        # 如果需要，可在此將 /api/v1/... 重寫為 /v1/...，或保持原樣
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
