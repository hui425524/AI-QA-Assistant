from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    project_id: uuid.UUID | None = None
    name: str = Field(default="未命名專案", min_length=1, max_length=120)
    requirement: str = Field(min_length=5, max_length=30000)

    @field_validator("requirement")
    @classmethod
    def reject_blank_requirement(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("需求內容不能為空白。")
        return value


class RubricCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    present: bool


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_score: int = Field(ge=0, le=100)
    readiness_state: Literal["blocked", "ready"]
    is_complete: bool
    missing_items: list[str] = Field(max_length=9)
    clarification_questions: list[str] = Field(max_length=5)
    checklist: list[RubricCheck] = Field(min_length=9, max_length=9)
    summary: str
    provider: str


class TestCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    scenario: str
    preconditions: str
    steps: list[str] = Field(min_length=1)
    test_data: str
    expected_result: str
    priority: Literal["High", "Medium", "Low"]
    test_type: str
