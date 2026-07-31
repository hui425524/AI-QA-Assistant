# AI QA Assistant 開發計畫

## 專案名稱

**AI QA Assistant**

## 專案目標

協助 QA 新手在撰寫測試案例前，先檢查需求是否完整。

若需求不明確，系統必須停止生成測試案例，並產生需求澄清問題；只有在需求足夠完整後，才能生成結構化測試案例。

## 目標使用者

1. QA 新手
2. 正在準備 QA 面試的人

## 核心問題

1. QA 新手不知道如何撰寫測試案例
2. 容易遺漏異常、邊界及權限情境
3. 測試案例格式整理耗時
4. 需求不完整時，AI 容易自行猜測並產生不可靠內容

## 核心流程

1. 使用者輸入完整需求文字
2. AI 分析需求完整性
3. 若需求不完整：
   - 顯示需求品質分數
   - 顯示缺少的資訊
   - 自動產生需求澄清問題
   - 完全禁止生成測試案例
4. 使用者補充需求後重新分析
5. 若需求完整：
   - 開放生成測試案例
6. 使用者可編輯、新增、刪除測試案例
7. 可儲存歷史紀錄
8. 可匯出 CSV

---

# MVP 功能

## 一、需求輸入

- 提供專案名稱欄位
- 提供大型文字輸入框
- 第一版只支援貼上文字
- 不需要支援 PDF 或 Word

## 二、需求完整性分析

檢查以下項目：

- 功能目標
- 使用者角色
- 前置條件
- 正常流程
- 錯誤處理
- 輸入限制
- 邊界條件
- 權限規則
- 預期結果

### 輸出格式

- `requirement_score`：0～100
- `is_complete`：true 或 false
- `missing_items`：缺少資訊清單
- `clarification_questions`：需求澄清問題清單
- `summary`：簡短分析說明

### 判斷規則

- 若 `is_complete` 為 false，禁止產生測試案例
- 不得自行假設缺少的需求
- 需要明確提醒使用者補充內容

## 三、需求澄清

例如需求為：

> 使用者可以登入系統

應產生類似問題：

- 帳號格式是否有限制？
- 密碼格式及長度限制為何？
- 登入失敗幾次後是否鎖定？
- 帳號未驗證時是否可以登入？
- 登入成功後跳轉至哪個頁面？
- Session 多久失效？
- 是否支援忘記密碼？

## 四、測試案例生成

只有需求完整時才能執行。

每筆測試案例需包含：

- `case_id`
- `scenario`
- `preconditions`
- `steps`
- `test_data`
- `expected_result`
- `priority`
- `test_type`

測試類型可包含：

- 正常流程
- 異常流程
- 邊界值
- 權限
- 輸入驗證
- 安全性

## 五、測試案例管理

- 表格顯示
- 可直接編輯
- 可新增
- 可刪除
- 可重新生成全部案例
- 第一版不需要單筆 AI 重新生成

## 六、歷史紀錄

使用 SQLite 儲存：

- 專案名稱
- 原始需求
- 補充後需求
- 分析結果
- 測試案例
- 建立時間
- 更新時間

## 七、匯出

- 匯出 CSV
- 欄位需包含所有測試案例欄位

---

# 建議技術

- Python
- Flask
- SQLite
- HTML
- Bootstrap
- Vanilla JavaScript
- AI API 抽象化為獨立 service
- 使用環境變數管理 API Key
- 提供 mock mode，沒有 API Key 時也能使用固定範例測試

---

# 頁面規劃

## 1. 首頁

- 專案名稱
- 需求輸入框
- 「分析需求」按鈕

## 2. 分析結果頁

- 需求品質分數
- 完整或不完整狀態
- 缺少資訊
- 需求澄清問題
- 補充需求輸入框
- 「重新分析」按鈕
- 若需求不完整，生成按鈕必須禁用

## 3. 測試案例頁

- 測試案例表格
- 編輯
- 新增
- 刪除
- 儲存
- 匯出 CSV

## 4. 歷史紀錄頁

- 顯示過去專案
- 可開啟查看

---

# 資料庫設計

## projects

- `id`
- `name`
- `original_requirement`
- `refined_requirement`
- `requirement_score`
- `is_complete`
- `analysis_json`
- `created_at`
- `updated_at`

## test_cases

- `id`
- `project_id`
- `case_id`
- `scenario`
- `preconditions`
- `steps`
- `test_data`
- `expected_result`
- `priority`
- `test_type`

---

# API 路由建議

- `GET /`
- `POST /api/analyze`
- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/<id>`
- `POST /api/projects/<id>/generate`
- `PUT /api/test-cases/<id>`
- `DELETE /api/test-cases/<id>`
- `GET /api/projects/<id>/export`

---

# AI 回傳格式

AI 回傳格式必須強制使用 JSON。

## 需求分析 JSON

```json
{
  "requirement_score": 65,
  "is_complete": false,
  "missing_items": [],
  "clarification_questions": [],
  "summary": ""
}
```

## 測試案例 JSON

```json
{
  "test_cases": [
    {
      "case_id": "TC001",
      "scenario": "",
      "preconditions": "",
      "steps": [],
      "test_data": "",
      "expected_result": "",
      "priority": "High",
      "test_type": "正常流程"
    }
  ]
}
```

---

# 開發順序

## Day 1

- 建立 Flask 專案
- 建立 SQLite
- 完成首頁
- 完成需求分析 API
- 建立 mock mode

## Day 2

- 完成分析結果頁
- 顯示缺少項目與澄清問題
- 完成阻擋生成邏輯

## Day 3

- 完成測試案例生成
- 完成測試案例表格
- 儲存資料

## Day 4

- 編輯、新增、刪除
- 歷史紀錄
- CSV 匯出

## Day 5

- 修正錯誤
- 補 README
- 加入範例需求
- 整理面試展示流程

---

# 驗收條件

1. 貼上不完整需求時，不可生成測試案例
2. 系統會指出缺少資訊並產生澄清問題
3. 補充需求後可重新分析
4. 完整需求可生成結構化測試案例
5. 測試案例可編輯、儲存及匯出 CSV
6. 沒有 API Key 時可使用 mock mode
7. 專案可透過 README 在本機成功啟動

---

# 請 Codex 優先完成

1. 專案資料夾架構
2. README
3. requirements.txt
4. SQLite schema
5. Flask 基礎程式
6. mock mode
7. 首頁與需求分析流程

請分階段實作，不要一次產生過多複雜功能。

每完成一個階段，請說明：

- 新增了哪些檔案
- 如何執行
- 如何測試
- 下一步要做什麼
