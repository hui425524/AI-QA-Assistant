# AI QA Assistant

AI QA Assistant 是一個「需求就緒閘門」。它先檢查需求是否包含目標、角色、流程、錯誤、限制、邊界、權限與預期結果；資訊不足時，前端、API 與資料庫都會阻止測試案例生成。

目前完成 Phase 1 vertical slice：

- 單頁需求分析 UI
- deterministic mock analyzer / generator
- `blocked` / `ready` server-side gate
- 不可變需求版本與案例追溯
- Supabase PostgreSQL migration
- SQLAlchemy 2 + psycopg 3 runtime connection
- liveness / readiness checks
- 統一錯誤格式與 request ID

## 3 分鐘 mock quickstart

先決條件：Python 3.11 以上。

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python run.py
```

開啟 <http://127.0.0.1:5000>。沒有設定 Supabase 時仍可試用需求分析；畫面會清楚標示「未保存」，生成按鈕不會開放。

執行測試：

```powershell
python -m pytest
```

## 連接 Supabase

1. 在 Supabase 建立 project。
2. 從 Dashboard 的 **Connect** 複製 direct connection；若執行環境只有 IPv4，長時間運行的 Flask server 使用 Session pooler（port 5432）。
3. 將 `.env` 的 `DATABASE_URL` 換成真實連線字串，密碼中的特殊字元需 URL encode，並保留 `sslmode=require`。
4. 依 [Supabase database migrations 官方流程](https://supabase.com/docs/guides/local-development/database-migrations) 套用 `supabase/migrations/202608010001_initial_schema.sql`：

```powershell
supabase login
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
```

5. 重新啟動 Flask，確認 readiness：

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health/ready
```

應回傳：

```json
{"database":"up","status":"ready"}
```

Supabase 官方對連線模式的說明請見 [Connect to your database](https://supabase.com/docs/guides/database/connecting-to-postgres)。本專案預設以小型 SQLAlchemy pool 服務持續運行的 Flask；若使用 transaction pooler（6543），程式會改用 `NullPool` 並停用 prepared statements。

## 環境變數

| 名稱 | 預設 | 用途 |
|---|---|---|
| `FLASK_DEBUG` | `1` in example | 本機 debug；部署時設 `0` |
| `DATABASE_URL` | placeholder | Supabase PostgreSQL 連線字串 |
| `AI_MODE` | `mock` | Phase 1 僅支援 `mock` |
| `AI_API_KEY` | 空白 | future live provider 使用 |
| `MAX_REQUIREMENT_CHARS` | `30000` | API 需求長度上限 |

`.env`、資料庫密碼與 API Key 都被 `.gitignore` 排除。不要把 requirement 全文寫進 production log。

## API

### `GET /health/live`

只確認 Flask 程序存活，不檢查資料庫。

### `GET /health/ready`

執行 `select 1`；沒有設定或無法連上 Supabase 時回 503。

### `POST /api/analyze`

```json
{
  "name": "會員登入",
  "requirement": "使用者可以登入系統",
  "project_id": null
}
```

設定資料庫後必須帶 `X-Workspace-ID: <uuid>`。重新分析同一專案時，把上一個 `project_id` 傳回，系統會建立下一個不可變需求版本。

### `POST /api/projects/<project_id>/generate`

不接受客戶端傳入 `is_complete`。API 只讀取資料庫中的最新版本；若它不是 `ready`，固定回：

```json
{
  "error": {
    "code": "REQUIREMENTS_BLOCKED",
    "message": "需求尚未完整，不能生成測試案例。",
    "details": {"missing_items": []},
    "request_id": "..."
  }
}
```

## 架構與安全邊界

```text
Browser → Flask validation/gate → analysis service
                         └──────→ SQLAlchemy/psycopg → Supabase PostgreSQL
```

- `projects`：匿名 workspace 邊界。
- `requirement_versions`：不可變需求與分析。
- `test_cases`：綁定一個 `ready` 需求版本。
- migration 對 public tables 啟用 RLS，並撤銷 `anon` / `authenticated` 直接存取。
- database trigger 會拒絕把案例寫入 blocked 版本。
- Phase 1 的 workspace UUID 是隔離鍵，不是登入或強身分驗證；公開多人版前必須完成 Supabase Auth 與 per-user RLS policy。

## 常見問題

`/health/ready` 回 `not_configured`：確認 `.env` 已複製且 `DATABASE_URL` 不是 placeholder，然後重啟 Flask。

Supabase 連線 timeout：direct connection 需要執行環境支援 IPv6；IPv4 環境改用 Dashboard 提供的 Session pooler 5432。

密碼驗證失敗：不要直接拼接含 `@`、`:`、`/` 等特殊字元的密碼；先 URL encode，並從 Dashboard 重新複製完整字串。

UI 顯示 ready 但不能生成：這代表 mock 分析通過、但資料尚未保存。確認 `/health/ready` 為 200 後重新分析。

## 下一階段

- Test case CRUD 與 CSV export
- 真 PostgreSQL integration / trigger / RLS tests
- generation run idempotency 與併發測試
- Supabase Auth 與 per-user RLS
- live AI provider 與 prompt/version audit
