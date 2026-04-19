---
inclusion: auto
description: "繁體中文語言偏好與文件維護規範"
---

# 編碼慣例

## 語言偏好

- **說明文件、註解、commit message 一律使用繁體中文**
- 變數名稱、函式名稱、類別名稱維持英文（程式碼本身不中文化）
- docstring、inline comment 使用中文
- steering 文件、README、spec 等文件使用中文撰寫
- 與使用者對話時使用中文

## 文件維護

- **新增重要功能後，主動更新 `.kiro/steering/` 中對應的文件**，包含：
  - 目錄結構變更
  - 新的資料表 / API 端點
  - 新的排程任務
  - 新的業務設定
  - 新的外部 API 資料來源
- 如果變更跨前後端，同時更新 `backend-guide.md` 和 `frontend-guide.md`
- 保持 steering 文件與實際程式碼同步，避免過時資訊
