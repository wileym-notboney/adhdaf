# ABOUTME: Pydantic models for API request/response validation.
# ABOUTME: Shared between routes — keeps serialization rules in one place.
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class CaptureRequest(BaseModel):
    raw: str
    source: Literal["web", "voice", "cli", "api"] = "voice"

    @field_validator("raw")
    @classmethod
    def raw_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("raw must not be empty")
        return stripped


class CaptureResponse(BaseModel):
    capture_id: str
    status: str
    task_ids: list[str] = []


class TaskOut(BaseModel):
    id: str
    capture_id: str | None = None
    title: str
    notes: str | None = None
    checklist: list[dict] | None = None
    status: str
    priority: str | None = None
    area: str | None = None
    tags: list[str] = []
    source: str
    position: int
    is_focus: bool
    due_at: datetime | None = None
    remind_at: datetime | None = None
    snoozed_until: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    version: str
