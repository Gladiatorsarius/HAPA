"""Validated request and response models for the public API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from src.core.schemas import (
    ExecutionLineage,
    NonEmptyText,
    ProvenanceMetadata,
    SchemaModel,
    TaskLifecycle,
)


class TaskRequest(SchemaModel):
    title: NonEmptyText
    description: str = ""
    requested_by: NonEmptyText
    labels: list[NonEmptyText] = Field(default_factory=list)
    callback_url: str | None = None

    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("callback_url must use http:// or https://")
        return value


class ChatMessageRequest(SchemaModel):
    message: NonEmptyText
    requested_by: NonEmptyText
    title: NonEmptyText = "Chat task"
    labels: list[NonEmptyText] = Field(default_factory=list)
    callback_url: str | None = None

    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("callback_url must use http:// or https://")
        return value


class ChatAcknowledgement(SchemaModel):
    model_config = {"strict": False}
    chat_id: UUID
    answer: NonEmptyText
    state: TaskLifecycle
    follow_up_url: str
    events_url: str
    callback_configured: bool


class ScheduleRequest(SchemaModel):
    title: NonEmptyText
    description: str = ""
    requested_by: NonEmptyText
    schedule_type: Literal["interval", "cron"]
    interval_seconds: int | None = Field(default=None, ge=1)
    cron_expression: str | None = None
    timezone: NonEmptyText = "UTC"
    callback_url: str | None = None

    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("callback_url must use http:// or https://")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be an IANA timezone") from exc
        return value

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, value: str | None) -> str | None:
        if value is not None:
            from croniter import croniter

            if not croniter.is_valid(value):
                raise ValueError("cron_expression is invalid")
        return value

    @model_validator(mode="after")
    def validate_schedule_fields(self) -> "ScheduleRequest":
        if self.schedule_type == "interval" and self.interval_seconds is None:
            raise ValueError("interval_seconds is required for interval schedules")
        if self.schedule_type == "cron" and self.cron_expression is None:
            raise ValueError("cron_expression is required for cron schedules")
        if self.schedule_type == "interval" and self.cron_expression is not None:
            raise ValueError("cron_expression is only valid for cron schedules")
        if self.schedule_type == "cron" and self.interval_seconds is not None:
            raise ValueError("interval_seconds is only valid for interval schedules")
        return self


class ScheduleResponse(SchemaModel):
    model_config = {"strict": False}
    schedule_id: UUID
    title: NonEmptyText
    description: str
    requested_by: NonEmptyText
    schedule_type: Literal["interval", "cron"]
    interval_seconds: int | None = None
    cron_expression: str | None = None
    timezone: NonEmptyText
    callback_url: str | None = None
    state: Literal["ACTIVE", "PAUSED", "CANCELLED"]
    next_run_at: datetime
    last_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApprovalDecision(SchemaModel):
    comment: str = ""


class TaskResponse(SchemaModel):
    model_config = {"strict": False}
    task_id: UUID
    title: NonEmptyText
    description: str = ""
    state: TaskLifecycle
    approval_required: bool
    lineage: ExecutionLineage
    provenance: ProvenanceMetadata
    created_at: datetime
    updated_at: datetime


class TelemetryEvent(SchemaModel):
    event_id: int | None = None
    task_id: UUID
    event_type: NonEmptyText
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
