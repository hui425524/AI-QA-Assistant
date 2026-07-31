from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_workspace_updated", "workspace_id", "updated_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    requirement_versions: Mapped[list["RequirementVersion"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="RequirementVersion.version",
    )


class RequirementVersion(Base):
    __tablename__ = "requirement_versions"
    __table_args__ = (
        CheckConstraint(
            "readiness_state in ('blocked', 'ready')",
            name="ck_requirement_versions_state",
        ),
        CheckConstraint(
            "requirement_score between 0 and 100",
            name="ck_requirement_versions_score",
        ),
        UniqueConstraint("project_id", "version", name="uq_requirement_project_version"),
        Index("ix_requirement_versions_project_version", "project_id", "version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    readiness_state: Mapped[str] = mapped_column(String(16), nullable=False)
    missing_items: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    clarification_questions: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    analysis_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="requirement_versions")
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="requirement_version",
        cascade="all, delete-orphan",
    )


class TestCase(Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        CheckConstraint(
            "priority in ('High', 'Medium', 'Low')", name="ck_test_cases_priority"
        ),
        UniqueConstraint(
            "requirement_version_id", "case_id", name="uq_test_case_version_case_id"
        ),
        Index("ix_test_cases_requirement_version", "requirement_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requirement_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("requirement_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[str] = mapped_column(String(30), nullable=False)
    scenario: Mapped[str] = mapped_column(String(240), nullable=False)
    preconditions: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    test_data: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(12), nullable=False)
    test_type: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    requirement_version: Mapped[RequirementVersion] = relationship(
        back_populates="test_cases"
    )
