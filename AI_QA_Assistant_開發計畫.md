<!-- /autoplan restore point: .gstack-state/projects/AI-QA-Assistant/main-autoplan-restore-20260801-004743.md -->

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

使用 Supabase PostgreSQL 儲存：

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
- Supabase PostgreSQL
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
- 建立 Supabase migration
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
4. Supabase PostgreSQL schema
5. Flask 基礎程式
6. mock mode
7. 首頁與需求分析流程

請分階段實作，不要一次產生過多複雜功能。

每完成一個階段，請說明：

- 新增了哪些檔案
- 如何執行
- 如何測試
- 下一步要做什麼

---

# gstack 優化後執行計畫

## 1. 產品定位與成功條件

唯一 MVP persona 是「小型產品團隊中，第一次需要獨立拆解需求的新手 QA」。面試準備者仍可使用，但不是第一階段優化對象。

核心價值不是更快產生更多測試案例，而是建立一個**可稽核的需求就緒閘門**：系統必須清楚說明哪些資訊缺失、為何阻擋、需要問什麼，且絕不以 AI 猜測補空白。

成功條件：

1. 新使用者可在 3 分鐘內完成「貼上需求 → 看見缺口 → 補充 → 再分析 → 生成案例」閉環。
2. 任何 `blocked` 需求直接呼叫生成 API 都回傳 `409 REQUIREMENTS_BLOCKED`，資料庫內新增案例數為 0。
3. 每批案例都能追溯到不可變的需求版本與分析結果。
4. AI 或 JSON 解析失敗時採 fail-closed：保留輸入、顯示可重試錯誤、禁止生成。
5. mock mode 在沒有 AI API Key 時仍能穩定重現完整與不完整兩條流程。

## 2. 已確認的產品決策

| 決策 | 結論 | 原因 |
|---|---|---|
| 不完整時能否先產生草稿案例 | 不允許 | 這是產品的信任契約；避免 UNKNOWN 被誤當成已確認規格 |
| 0–100 分是否控制生成 | 不控制 | 分數只供理解；唯一權威是後端計算的 `blocked` / `ready` 狀態 |
| SQLite 或 Supabase | 僅 Supabase PostgreSQL | 避免 demo 與正式環境雙資料庫行為分叉；本機無 DB 時僅能試用 mock 分析 |
| 首版是否做完整 CRUD／歷史頁 | 延後 | 先完成最小但完整的需求閘門 vertical slice |
| 首版是否導入 Supabase Auth | 延後 | 第一階段不開放瀏覽歷史；以匿名 workspace token 隔離請求，正式多人版再導入 Auth + RLS policy |
| migration 工具 | Supabase SQL migrations | 單一 schema 真相來源，避免同時維護 Alembic 與 Supabase migration |

## 3. 第一個 Product Lake：可稽核需求閘門

### In scope

1. 單頁輸入專案名稱與需求文字。
2. mock analyzer 檢查九類需求資訊，輸出嚴格 JSON schema。
3. 顯示 `blocked` / `ready`、缺漏項、最多五個澄清問題、輔助分數、分析模式與版本。
4. 補充原需求後重新分析，建立新的不可變需求版本。
5. Supabase PostgreSQL migration 與 SQLAlchemy 2 / psycopg 3 連線。
6. 伺服器端與資料庫端共同阻擋未就緒需求生成案例。
7. ready 時以 mock provider 生成可追溯案例並儲存。
8. `/health/live` 與 `/health/ready`、統一錯誤格式、request ID。
9. 單元與 API 測試涵蓋成功、驗證錯誤、DB 未設定、blocked 生成、版本追溯。

### Not in scope

- PDF／Word、Jira、Confluence、Figma 匯入。
- 完整測試案例 CRUD、歷史瀏覽、CSV 匯出。
- Supabase Auth、多人協作、角色權限。
- 真實 AI provider、串流回應、成本儀表板。
- 自動執行測試、轉換 Playwright／Cypress。

## 4. UX 與狀態規格

首頁採單頁漸進流程，桌面為輸入與結果雙欄，手機為單欄；不再要求使用者在四個頁面間來回切換。

資訊順序固定為：**狀態 → 下一步 → 缺漏 → 澄清問題 → 分數與技術細節**。生成區常駐並顯示鎖定原因，不能只用 disabled 樣式表示。

| 狀態 | 顯示內容 | 可用動作 |
|---|---|---|
| idle | 範例與輸入提示 | 檢查需求完整性 |
| loading | 保留輸入、阻止重複送出 | 等待／取消後重試 |
| blocked | 「尚缺 N 項，暫不能生成」、缺漏與澄清問題 | 編輯後重新檢查 |
| ready | 就緒原因、版本、provider | 生成測試案例 |
| error | 錯誤碼、request ID、修復指引，輸入不清空 | 重試 |
| offline | 保留本機草稿，停止送出 | 恢復連線後重試 |

可及性驗收：鍵盤可完成完整流程、結果標題取得焦點、狀態使用 `aria-live`、錯誤與欄位關聯、顏色不是唯一訊號、320px 無橫向捲動、200% 縮放可操作。

## 5. 工程架構

```text
Browser (workspace token)
        |
        v
Flask API -- request validation / error envelope / request ID
        |
        +--> Analysis service --> mock provider (future: live provider)
        |
        +--> Project service --> SQLAlchemy 2 --> psycopg 3
                                               |
                                               v
                                      Supabase PostgreSQL
```

資料模型採三張表：

1. `projects`：專案與匿名 workspace 邊界。
2. `requirement_versions`：不可變需求文字、版本、分數、`blocked|ready`、完整分析 JSON、provider。
3. `test_cases`：綁定 `requirement_version_id`，包含結構化步驟與來源版本。

資料庫 trigger 在 `test_cases` insert/update 時再次檢查需求版本必須是 `ready`。即使 API 有缺陷，也不能把 blocked 需求寫成案例。

生成 API 只讀取資料庫中的最新需求版本，不接受客戶端傳入 `is_complete`。同一需求版本重新生成採可重現覆寫，唯一鍵為 `(requirement_version_id, case_id)`。

### API 契約

- `GET /health/live`：程序存活，永遠不碰 DB。
- `GET /health/ready`：執行 `select 1`；未設定或連線失敗回 503。
- `POST /api/analyze`：驗證並分析需求；DB 可用時建立專案／新需求版本。
- `POST /api/projects/<uuid>/generate`：只對最新 `ready` 版本生成；blocked 回 409。

錯誤統一為：

```json
{
  "error": {
    "code": "REQUIREMENTS_BLOCKED",
    "message": "需求尚未完整，不能生成測試案例。",
    "details": {},
    "request_id": "..."
  }
}
```

### Supabase 連線策略

- 長時間運行的 Flask server 優先用 direct connection；僅 IPv4 時用 Supavisor session mode 5432。
- Runtime 使用小型 `QueuePool`、`pool_pre_ping`；不使用 transaction pooler 的 prepared statements。
- `DATABASE_URL`、DB 密碼與未來 AI Key 只放部署 secret／本機 `.env`，不得提交。
- public tables 啟用 RLS 且不建立 anon/authenticated policy，避免前端經 Data API 直接讀取；第一階段只允許 Flask 後端連線。
- schema 只透過 `supabase/migrations/*.sql` 演進。

## 6. 測試策略

```text
大量：純函式單元測試（rubric、schema、狀態轉移、mock 穩定性）
中量：Flask API 測試（validation、錯誤 envelope、request ID、blocked 409）
少量：Supabase/PostgreSQL 整合測試（migration、trigger、RLS、連線失敗）
一條 E2E：不完整 → 補充 → ready → 生成
```

必測負例：空白、過短／過長需求、AI 非法 JSON、DB 未設定、錯誤 workspace token、舊版本生成、blocked 直接生成、重複生成、跨 workspace 專案 ID。

## 7. DX 規格

目標 persona 是熟悉基礎 Python 的 QA／作品集開發者。Hello World 不要求 Supabase：mock 分析可在 3 分鐘內啟動；要驗證持久化與生成時才需要設定 `DATABASE_URL`。

README 必須包含：先決條件、五個命令內 quickstart、環境變數、Supabase 建立與 migration、範例需求、預期回應、健康檢查、常見錯誤、測試命令、架構與安全限制。

環境變數最少為：

- `FLASK_DEBUG`
- `DATABASE_URL`
- `AI_MODE=mock`
- `AI_API_KEY`（future/live 才需要）
- `MAX_REQUIREMENT_CHARS`

## 8. 分階段執行

### Phase 1 — Foundation + gate（本次開始）

- Flask app factory、設定與錯誤 envelope。
- Supabase migration、SQLAlchemy models／repository。
- deterministic mock analyzer 與 generator。
- 單頁 UI、分析 API、後端 blocked gate。
- health checks、README、`.env.example`、測試。

### Phase 2 — Test case workflow

- 案例列表、編輯、新增、刪除。
- CSV 匯出與 generation run idempotency。
- 真 PostgreSQL integration test 與併發測試。

### Phase 3 — Multi-user trust

- Supabase Auth、每位使用者 RLS policy、歷史頁。
- 真實 AI provider、prompt/version audit、成本與延遲指標。

### Phase 4 — Integrations

- Jira／Confluence／文件匯入、TestRail／Qase 匯出。

## 9. 風險與失敗模式

| 風險 | 防護 | 驗收 |
|---|---|---|
| 假通過 | fail-closed、黃金測資、ready 必須滿足必要類別 | 重大缺口攔截率目標 ≥90% |
| 假阻擋 | 問題最多五個、允許明示 N/A | 真實需求可在一次補充後改善狀態 |
| AI 漂移／非法 JSON | Pydantic schema、provider/version 記錄 | 解析失敗零案例 |
| 提示注入 | 需求只當資料、固定 system contract | 測資中的指令不能改變 JSON schema |
| 機密資料 | UI 警示、日誌不記需求全文 | log 掃描無需求與秘密 |
| DB 不可用 | ready health、503、分析仍可 mock | 輸入不遺失且錯誤可修復 |
| 前端繞過 | API gate + DB trigger | blocked insert/API 雙重失敗 |

## 10. 決策稽核

- CEO 審查建議把 blocked 案例降級為帶 UNKNOWN 的草稿；因與明確產品契約衝突，決定不採用。
- CEO／DX 審查建議先延後 Supabase 或保留 SQLite demo；因本次明確要求連接 Supabase，且雙資料庫會增加漂移，決定直接採 PostgreSQL，無 DB 時只提供無持久化 mock 分析。
- 工程審查建議首版加入 Auth、generation runs、完整併發控制；為維持 Product Lake 完整且可交付，Auth 與 run orchestration 延後，但保留版本化 schema、API gate、DB trigger 與 workspace scope。
- 設計審查建議同頁流程、狀態優先、分數次要、需求版本可追溯；全部採用。
- 競品（TestRail、BrowserStack、Qase）已能從需求產生案例；本產品不以「生成」差異化，而以「阻擋不可靠輸入、明確補問、版本追溯」差異化。

## GSTACK REVIEW REPORT

### CEO Review

- 計畫摘要：可稽核需求就緒閘門，而非通用案例生成器。
- 前提挑戰：客群已收斂；分數降為輔助；硬閘門因產品契約保留。
- 替代方案：提示詞／通用 LLM、現有 TMS AI、先無持久化；選擇 Supabase-backed vertical slice。
- 主要風險：假通過、假阻擋、輸出漂移、資料機密、差異化不足。

### Design Review

- 7 個面向：Hierarchy 8/10、Flow 8/10、States 9/10、Copy 8/10、Accessibility 8/10、Responsive 8/10、Trust 9/10。
- 關鍵修正：同頁漸進、狀態先於分數、鎖定原因常駐、六態完整、版本與 provider 可見。

### Engineering Review

- 架構：Flask → service/repository → SQLAlchemy/psycopg → Supabase PostgreSQL。
- 關鍵不變量：生成只讀最新 server-side analysis；API 與 DB trigger 雙重 fail-closed。
- 資料：projects / requirement_versions / test_cases，案例綁定不可變需求版本。
- 運維：版本化 migrations、小型連線池、readiness check、request ID、結構化錯誤。

### DX Review

- 目標 TTHW：mock 分析 ≤3 分鐘，Supabase-backed flow ≤15 分鐘（不含建立雲端專案等待時間）。
- 最大摩擦：DB 設定、mock/live 模式、migration 與診斷入口。
- 修正：五命令 quickstart、完整 `.env.example`、兩種 health endpoint、範例與預期輸出、單一 migration 系統。

### Cross-phase Themes

1. Trust before generation：任何失敗都不能偷偷降級成案例。
2. State before score：狀態控制流程，分數只輔助理解。
3. Traceability by default：分析與案例都綁定不可變需求版本。
4. One database truth：Supabase PostgreSQL 是唯一持久化實作。
5. Small complete lake：先完成可操作閉環，再加 CRUD、Auth 與整合。

### Aggregated Tasks

- [P0] Scaffold Flask app、設定、request ID 與錯誤 envelope。
- [P0] 建立 Supabase migration、RLS deny-by-default、ready trigger。
- [P0] 實作 deterministic mock analyzer／generator 與 JSON schema。
- [P0] 實作 `/api/analyze`、`/api/projects/<id>/generate` 的 server-side gate。
- [P0] 建立單頁 UI 與六種狀態。
- [P0] 測試 blocked 409、DB not configured、schema、health 與版本追溯。
- [P1] Test case CRUD、CSV、真 PostgreSQL integration／併發測試。
- [P1] Supabase Auth + per-user RLS。
- [P2] live AI provider、外部 TMS 整合。

### Final Gate

- 計畫完整性：PASS
- Product Lake 完整性：PASS
- UI scope review：PASS（文字版；本環境無 gstack design binary）
- DX scope review：PASS
- Merge-only Git safety：PASS（base `main` 固定於 `a118b29`，實作分支 `feat/supabase-mvp`）
- 剩餘阻塞：無；live Supabase handshake 需要部署時提供 `DATABASE_URL`，不阻擋程式與 migration 實作。

NO UNRESOLVED DECISIONS
