from __future__ import annotations

import uuid

import pytest

from app import create_app


@pytest.fixture()
def app():
    return create_app(
        {
            "TESTING": True,
            "DATABASE_URL": "sqlite+pysqlite:///:memory:",
            "CREATE_SCHEMA": True,
            "AI_MODE": "mock",
            "MAX_REQUIREMENT_CHARS": 30000,
        }
    )


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def workspace_headers():
    return {"X-Workspace-ID": str(uuid.uuid4())}


@pytest.fixture()
def complete_requirement():
    return """功能目標：讓會員能以電子郵件與密碼登入並進入個人首頁。
使用者角色：已註冊且啟用的會員；管理員遵循相同登入流程。
前置條件：帳號已完成驗證，使用者目前未登入。
正常流程：使用者輸入電子郵件與密碼，點擊登入，系統驗證成功後建立 Session。
錯誤處理：帳密無效時顯示錯誤訊息；連續失敗五次鎖定十五分鐘。
輸入限制：電子郵件必填且符合格式；密碼必填，長度 8 到 64 字元。
邊界條件：密碼最少 8、最多 64 字元；Session 最多 30 分鐘未操作即失效。
權限規則：只有啟用會員可登入；停權、未驗證或已刪除帳號不可登入。
預期結果：登入成功應導向 /dashboard、更新最後登入時間並設定 HttpOnly cookie。"""
