from __future__ import annotations

import uuid

from flask import Blueprint, current_app, g, jsonify, render_template, request
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError

from .db import database_ready, get_engine, session_scope
from .errors import AppError
from .models import Project, RequirementVersion, TestCase, utc_now
from .qa_service import get_provider
from .schemas import AnalyzeRequest


web = Blueprint("web", __name__)
api = Blueprint("api", __name__, url_prefix="/api")
health = Blueprint("health", __name__, url_prefix="/health")


def _workspace_id(required: bool) -> uuid.UUID | None:
    raw_value = request.headers.get("X-Workspace-ID", "").strip()
    if not raw_value and not required:
        return None
    try:
        return uuid.UUID(raw_value)
    except (ValueError, AttributeError):
        raise AppError(
            "INVALID_WORKSPACE_ID",
            "X-Workspace-ID 必須是有效 UUID。",
            400,
        ) from None


@web.get("/")
def index():
    return render_template("index.html")


@health.get("/live")
def live():
    return jsonify({"status": "up"})


@health.get("/ready")
def ready():
    is_ready, database_status = database_ready()
    response = jsonify(
        {
            "status": "ready" if is_ready else "not_ready",
            "database": database_status,
        }
    )
    response.status_code = 200 if is_ready else 503
    return response


@api.post("/analyze")
def analyze():
    body = request.get_json(silent=True)
    if body is None:
        raise AppError("INVALID_JSON", "請提供 JSON request body。", 400)

    payload = AnalyzeRequest.model_validate(body)
    if len(payload.requirement) > current_app.config["MAX_REQUIREMENT_CHARS"]:
        raise AppError(
            "REQUIREMENT_TOO_LONG",
            "需求內容超過允許長度。",
            422,
            {"max_chars": current_app.config["MAX_REQUIREMENT_CHARS"]},
        )

    provider = get_provider(current_app.config["AI_MODE"])
    analysis = provider.analyze(payload.requirement)
    response_data = analysis.model_dump()
    response_data.update(project_id=None, requirement_version=None, persisted=False)

    if get_engine() is None:
        return jsonify(response_data)

    workspace_id = _workspace_id(required=True)
    try:
        with session_scope() as session, session.begin():
            if payload.project_id is None:
                project = Project(workspace_id=workspace_id, name=payload.name)
                session.add(project)
                session.flush()
                next_version = 1
            else:
                project = session.scalar(
                    select(Project)
                    .where(
                        Project.id == payload.project_id,
                        Project.workspace_id == workspace_id,
                    )
                    .with_for_update()
                )
                if project is None:
                    raise AppError("PROJECT_NOT_FOUND", "找不到此專案。", 404)
                project.name = payload.name
                project.updated_at = utc_now()
                latest = session.scalar(
                    select(func.max(RequirementVersion.version)).where(
                        RequirementVersion.project_id == project.id
                    )
                )
                next_version = (latest or 0) + 1

            requirement_version = RequirementVersion(
                project_id=project.id,
                version=next_version,
                requirement_text=payload.requirement,
                requirement_score=analysis.requirement_score,
                readiness_state=analysis.readiness_state,
                missing_items=analysis.missing_items,
                clarification_questions=analysis.clarification_questions,
                analysis_json=analysis.model_dump(),
                provider=analysis.provider,
            )
            session.add(requirement_version)
            session.flush()
            response_data.update(
                project_id=str(project.id),
                requirement_version=next_version,
                persisted=True,
            )
    except AppError:
        raise
    except SQLAlchemyError as error:
        current_app.logger.exception(
            "Analysis persistence failed request_id=%s", g.request_id
        )
        raise AppError(
            "DATABASE_UNAVAILABLE",
            "分析已完成，但目前無法寫入 Supabase，請稍後重試。",
            503,
        ) from error

    return jsonify(response_data)


@api.post("/projects/<uuid:project_id>/generate")
def generate(project_id: uuid.UUID):
    if get_engine() is None:
        raise AppError(
            "DATABASE_NOT_CONFIGURED",
            "尚未設定 Supabase DATABASE_URL，無法生成並保存案例。",
            503,
        )

    workspace_id = _workspace_id(required=True)
    try:
        with session_scope() as session:
            project_exists = session.scalar(
                select(Project.id).where(
                    Project.id == project_id,
                    Project.workspace_id == workspace_id,
                )
            )
            if project_exists is None:
                raise AppError("PROJECT_NOT_FOUND", "找不到此專案。", 404)

            latest = session.scalar(
                select(RequirementVersion)
                .where(RequirementVersion.project_id == project_id)
                .order_by(RequirementVersion.version.desc())
                .limit(1)
            )
            if latest is None:
                raise AppError("ANALYSIS_NOT_FOUND", "此專案尚未分析。", 409)
            if latest.readiness_state != "ready":
                raise AppError(
                    "REQUIREMENTS_BLOCKED",
                    "需求尚未完整，不能生成測試案例。",
                    409,
                    {
                        "requirement_version": latest.version,
                        "missing_items": latest.missing_items,
                    },
                )
            requirement_version_id = latest.id
            requirement_version_number = latest.version
            requirement_text = latest.requirement_text

        provider = get_provider(current_app.config["AI_MODE"])
        generated = provider.generate(requirement_text)

        with session_scope() as session, session.begin():
            current_latest = session.scalar(
                select(RequirementVersion)
                .where(RequirementVersion.project_id == project_id)
                .order_by(RequirementVersion.version.desc())
                .limit(1)
                .with_for_update()
            )
            if current_latest is None or current_latest.id != requirement_version_id:
                raise AppError(
                    "REQUIREMENT_VERSION_CHANGED",
                    "需求已更新，請重新確認分析結果後再生成。",
                    409,
                )
            if current_latest.readiness_state != "ready":
                raise AppError(
                    "REQUIREMENTS_BLOCKED",
                    "需求尚未完整，不能生成測試案例。",
                    409,
                )

            session.execute(
                delete(TestCase).where(
                    TestCase.requirement_version_id == requirement_version_id
                )
            )
            rows = [
                TestCase(
                    requirement_version_id=requirement_version_id,
                    **test_case.model_dump(),
                )
                for test_case in generated
            ]
            session.add_all(rows)
            session.flush()
            response_cases = [
                {"id": str(row.id), **test_case.model_dump()}
                for row, test_case in zip(rows, generated, strict=True)
            ]
    except AppError:
        raise
    except SQLAlchemyError as error:
        current_app.logger.exception(
            "Generation persistence failed request_id=%s", g.request_id
        )
        raise AppError(
            "DATABASE_UNAVAILABLE",
            "目前無法存取 Supabase，請稍後重試。",
            503,
        ) from error

    return jsonify(
        {
            "project_id": str(project_id),
            "requirement_version": requirement_version_number,
            "provider": provider.name,
            "test_cases": response_cases,
        }
    )
