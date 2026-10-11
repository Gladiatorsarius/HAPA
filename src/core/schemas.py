"""Strict Pydantic v2 schemas used for communication between HAPA tiers."""

from __future__ import annotations

from datetime import datetime
from enum import Enum, IntEnum, StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Tier(IntEnum):
    """Operational tier that produces or consumes a hand-off."""

    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class TaskLifecycle(StrEnum):
    """Allowed states in a task execution lifecycle."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    BLOCKED_AT_HUMAN_GATE = "BLOCKED_AT_HUMAN_GATE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DiffKind(StrEnum):
    """Kind of workspace change represented by a code diff."""

    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    RENAMED = "RENAMED"


class TestOutcome(StrEnum):
    """Outcome of an individual test or test suite."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class ReviewPersona(StrEnum):
    """Perspective used to review a code change."""

    SECURITY_AUDITOR = "SECURITY_AUDITOR"
    PERFORMANCE_OPTIMIZER = "PERFORMANCE_OPTIMIZER"
    EDGE_CASE_TESTER = "EDGE_CASE_TESTER"
    CODE_QUALITY_REVIEWER = "CODE_QUALITY_REVIEWER"
    API_CONTRACT_REVIEWER = "API_CONTRACT_REVIEWER"


class SchemaModel(BaseModel):
    """Common strict configuration for all wire models."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_assignment=True,
        use_enum_values=False,
    )


NonEmptyText = Annotated[str, Field(min_length=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]
Percentage = Annotated[float, Field(ge=0, le=100)]


class TaskMetadata(SchemaModel):
    """Identity and descriptive metadata for a task."""

    task_id: UUID = Field(default_factory=uuid4)
    title: NonEmptyText
    description: str = ""
    created_at: datetime
    deadline: datetime | None = None
    labels: list[NonEmptyText] = Field(default_factory=list)


class ExecutionLineage(SchemaModel):
    """Traceability information for a task as it crosses HAPA tiers."""

    correlation_id: UUID = Field(default_factory=uuid4)
    parent_task_id: UUID | None = None
    root_task_id: UUID
    hop_number: NonNegativeInt = 0
    requested_by: NonEmptyText
    preceding_handoff_id: UUID | None = None


class ExecutionSummary(SchemaModel):
    """Concise, human-readable result of an execution."""

    headline: NonEmptyText
    outcome: TaskLifecycle
    details: str = ""
    completed_steps: list[NonEmptyText] = Field(default_factory=list)
    unresolved_items: list[NonEmptyText] = Field(default_factory=list)
    recommendations: list[NonEmptyText] = Field(default_factory=list)
    generated_at: datetime


class TaskStatus(SchemaModel):
    """Current execution state and failure/retry information."""

    state: TaskLifecycle = TaskLifecycle.PENDING
    error_code: NonEmptyText | None = None
    failure_reason: str | None = None
    retry_count: NonNegativeInt = 0
    max_retries: NonNegativeInt = 0
    updated_at: datetime

    @model_validator(mode="after")
    def validate_failure_and_retries(self) -> TaskStatus:
        if self.state == TaskLifecycle.FAILED and not self.failure_reason:
            raise ValueError("failure_reason is required when state is FAILED")
        if self.state != TaskLifecycle.FAILED and self.failure_reason is not None:
            raise ValueError("failure_reason is only valid when state is FAILED")
        if self.retry_count > self.max_retries and self.state != TaskLifecycle.SUCCESS:
            raise ValueError("retry_count cannot exceed max_retries")
        return self


class WorkspaceFileDelta(SchemaModel):
    """A single file change in a workspace delta."""

    path: NonEmptyText
    kind: DiffKind
    patch: NonEmptyText | None = None
    old_path: NonEmptyText | None = None
    content_sha256: Annotated[str, Field(pattern=r"^[0-9a-fA-F]{64}$")] | None = None

    @model_validator(mode="after")
    def validate_delta(self) -> WorkspaceFileDelta:
        if self.kind in {DiffKind.ADDED, DiffKind.MODIFIED, DiffKind.DELETED} and not self.patch:
            raise ValueError("patch is required for added, modified, and deleted files")
        if self.kind == DiffKind.RENAMED and not self.old_path:
            raise ValueError("old_path is required for renamed files")
        if self.kind != DiffKind.RENAMED and self.old_path is not None:
            raise ValueError("old_path is only valid for renamed files")
        return self


class CodeDiffPayload(SchemaModel):
    """Validated source-control changes produced by an execution agent."""

    repository: NonEmptyText
    base_revision: NonEmptyText
    head_revision: NonEmptyText | None = None
    files: list[WorkspaceFileDelta] = Field(min_length=1)
    unified_diff: NonEmptyText | None = None
    is_cleanly_applicable: bool = True
    generated_at: datetime


class TestCaseResult(SchemaModel):
    """Result for one automated test or test suite."""

    name: NonEmptyText
    outcome: TestOutcome
    duration_ms: Annotated[float, Field(ge=0)] = 0
    message: str | None = None
    report_url: str | None = None


class ReviewFinding(SchemaModel):
    """A finding from one multi-perspective QA reviewer."""

    persona: ReviewPersona
    title: NonEmptyText
    description: NonEmptyText
    severity: Annotated[int, Field(ge=1, le=5)] = 3
    file_path: NonEmptyText | None = None
    line_start: NonNegativeInt | None = None
    line_end: NonNegativeInt | None = None
    recommendation: str | None = None
    blocking: bool = False

    @model_validator(mode="after")
    def validate_line_range(self) -> ReviewFinding:
        if (
            self.line_start is not None
            and self.line_end is not None
            and self.line_end < self.line_start
        ):
            raise ValueError("line_end cannot be before line_start")
        return self


class TestReport(SchemaModel):
    """Automated test results plus structured persona-based review findings."""

    suite_name: NonEmptyText
    outcome: TestOutcome
    total_tests: NonNegativeInt
    passed_tests: NonNegativeInt = 0
    failed_tests: NonNegativeInt = 0
    skipped_tests: NonNegativeInt = 0
    test_cases: list[TestCaseResult] = Field(default_factory=list)
    review_findings: list[ReviewFinding] = Field(default_factory=list)
    coverage_percent: Percentage | None = None
    summary: ExecutionSummary | None = None
    generated_at: datetime

    @model_validator(mode="after")
    def validate_counts(self) -> TestReport:
        counted = self.passed_tests + self.failed_tests + self.skipped_tests
        if counted > self.total_tests:
            raise ValueError("passed, failed, and skipped tests cannot exceed total_tests")
        if self.outcome == TestOutcome.PASSED and self.failed_tests:
            raise ValueError("a PASSED report cannot contain failed tests")
        return self


class TaskHandOff(SchemaModel):
    """Standardized payload exchanged between HAPA operational tiers."""

    handoff_id: UUID = Field(default_factory=uuid4)
    metadata: TaskMetadata
    lineage: ExecutionLineage
    origin_tier: Tier
    destination_tier: Tier
    status: TaskStatus
    payload: dict[str, Any] = Field(default_factory=dict)
    summary: ExecutionSummary | None = None
    code_diff: CodeDiffPayload | None = None
    test_report: TestReport | None = None
    created_at: datetime

    @model_validator(mode="after")
    def validate_tier_direction(self) -> TaskHandOff:
        if self.origin_tier == self.destination_tier:
            raise ValueError("origin_tier and destination_tier must differ")
        if self.code_diff is not None and self.origin_tier != Tier.TIER_3:
            raise ValueError("code_diff may only originate from TIER_3")
        return self
