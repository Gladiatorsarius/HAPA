"""Validated request and response models for the public API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

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


class ChatMessageRequest(SchemaModel):
    message: NonEmptyText
    requested_by: NonEmptyText
    title: NonEmptyText = "Chat task"
    labels: list[NonEmptyText] = Field(default_factory=list)


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
