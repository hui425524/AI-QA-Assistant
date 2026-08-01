from __future__ import annotations

import uuid
from pathlib import Path

from app import create_app


def test_homepage_exposes_template_and_direct_file_guidance(client):
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "需求撰寫範本" in html
    assert "功能目標：[要解決什麼問題、完成什麼任務]" in html
    assert "套用完整登入範例" in html
    assert "start_ai_qa_assistant.cmd" in html

    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'href="../static/styles.css"' in template
    assert 'src="../static/app.js"' in template
    assert "{{ url_for" not in template
    assert Path("start_ai_qa_assistant.cmd").is_file()


def _analyze(client, headers, requirement, project_id=None):
    body = {"name": "登入功能", "requirement": requirement}
    if project_id:
        body["project_id"] = project_id
    return client.post("/api/analyze", json=body, headers=headers)


def test_liveness_does_not_require_database():
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": "",
            "AI_MODE": "mock",
            "CREATE_SCHEMA": False,
        }
    )
    client = app.test_client()

    assert client.get("/health/live").status_code == 200
    readiness = client.get("/health/ready")
    assert readiness.status_code == 503
    assert readiness.get_json()["database"] == "not_configured"


def test_analysis_without_database_is_useful_but_not_persisted():
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": "",
            "AI_MODE": "mock",
            "CREATE_SCHEMA": False,
        }
    )
    response = app.test_client().post(
        "/api/analyze",
        json={"name": "Demo", "requirement": "使用者可以登入系統"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["readiness_state"] == "blocked"
    assert data["persisted"] is False
    assert data["project_id"] is None


def test_validation_error_has_request_id(client, workspace_headers):
    response = _analyze(client, workspace_headers, "太短")

    assert response.status_code == 422
    error = response.get_json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["request_id"] == response.headers["X-Request-ID"]


def test_blocked_requirement_cannot_generate(client, workspace_headers):
    analysis = _analyze(client, workspace_headers, "使用者可以登入系統")
    assert analysis.status_code == 200
    project_id = analysis.get_json()["project_id"]

    response = client.post(
        f"/api/projects/{project_id}/generate",
        headers=workspace_headers,
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "REQUIREMENTS_BLOCKED"


def test_ready_requirement_generates_versioned_cases(
    client, workspace_headers, complete_requirement
):
    analysis = _analyze(client, workspace_headers, complete_requirement)
    data = analysis.get_json()
    assert data["readiness_state"] == "ready"
    assert data["requirement_version"] == 1

    generated = client.post(
        f"/api/projects/{data['project_id']}/generate",
        headers=workspace_headers,
    )

    assert generated.status_code == 200
    output = generated.get_json()
    assert output["requirement_version"] == 1
    assert len(output["test_cases"]) == 3


def test_latest_blocked_version_invalidates_previous_ready_analysis(
    client, workspace_headers, complete_requirement
):
    ready = _analyze(client, workspace_headers, complete_requirement).get_json()
    blocked = _analyze(
        client,
        workspace_headers,
        "使用者可以登入系統",
        project_id=ready["project_id"],
    ).get_json()

    assert blocked["requirement_version"] == 2
    response = client.post(
        f"/api/projects/{ready['project_id']}/generate",
        headers=workspace_headers,
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "REQUIREMENTS_BLOCKED"


def test_workspace_boundary_hides_project(
    client, workspace_headers, complete_requirement
):
    project = _analyze(client, workspace_headers, complete_requirement).get_json()
    other_workspace = {"X-Workspace-ID": str(uuid.uuid4())}

    response = client.post(
        f"/api/projects/{project['project_id']}/generate",
        headers=other_workspace,
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "PROJECT_NOT_FOUND"
