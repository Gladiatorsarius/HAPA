"""Temporal workflow for durable, periodic Git workspace checkpoints."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Final
from uuid import UUID, uuid4

from pydantic import Field
from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from src.core.schemas import CodeDiffPayload, SchemaModel
    from src.persistence.git_handler import (
        GitWorkspaceHandler,
        NoWorkspaceChangesError,
    )


DEFAULT_SNAPSHOT_INTERVAL_SECONDS: Final[int] = 5
SNAPSHOT_ACTIVITY_TIMEOUT: Final[timedelta] = timedelta(minutes=1)


class SnapshotStatus(StrEnum):
    """Result of one checkpoint attempt."""

    CAPTURED = "CAPTURED"
    NO_CHANGES = "NO_CHANGES"


class SnapshotRecord(SchemaModel):
    """Durable record written for every checkpoint attempt."""

    checkpoint_id: UUID = Field(default_factory=uuid4)
    status: SnapshotStatus
    workspace: str
    base_revision: str
    captured_at: datetime
    diff: CodeDiffPayload | None = None


def _checkpoint_path(snapshot_dir: Path, record: SnapshotRecord) -> Path:
    timestamp = record.captured_at.astimezone(timezone.utc).strftime(
        "%Y%m%dT%H%M%S.%fZ"
    )
    return snapshot_dir / f"checkpoint-{timestamp}-{record.checkpoint_id}.json"


def _write_checkpoint(snapshot_dir: Path, record: SnapshotRecord) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    destination = _checkpoint_path(snapshot_dir, record)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=snapshot_dir,
        text=True,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file_handle:
            file_handle.write(record.model_dump_json(indent=2))
            file_handle.write("\n")
            file_handle.flush()
            os.fsync(file_handle.fileno())
        os.replace(temporary_name, destination)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return destination


@activity.defn
async def capture_snapshot(
    workspace: str,
    snapshot_dir: str,
    base_revision: str = "HEAD",
) -> dict[str, str]:
    """Capture the current workspace and atomically persist its checkpoint."""

    captured_at = datetime.now(timezone.utc)
    handler = GitWorkspaceHandler(workspace)
    try:
        try:
            diff = handler.capture_diff(base_revision)
        except NoWorkspaceChangesError:
            record = SnapshotRecord(
                status=SnapshotStatus.NO_CHANGES,
                workspace=str(Path(workspace).resolve()),
                base_revision=base_revision,
                captured_at=captured_at,
            )
        else:
            record = SnapshotRecord(
                status=SnapshotStatus.CAPTURED,
                workspace=str(Path(workspace).resolve()),
                base_revision=diff.base_revision,
                captured_at=captured_at,
                diff=diff,
            )
        path = _write_checkpoint(Path(snapshot_dir), record)
    finally:
        handler.close()

    return {
        "checkpoint_id": str(record.checkpoint_id),
        "path": str(path),
        "status": record.status.value,
    }


@workflow.defn
class SnapshotWorkflow:
    """Run checkpoint attempts until the workflow is cancelled."""

    @workflow.run
    async def run(
        self,
        workspace: str,
        snapshot_dir: str,
        interval_seconds: int = DEFAULT_SNAPSHOT_INTERVAL_SECONDS,
        base_revision: str = "HEAD",
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        while True:
            await workflow.execute_activity(
                capture_snapshot,
                args=[workspace, snapshot_dir, base_revision],
                start_to_close_timeout=SNAPSHOT_ACTIVITY_TIMEOUT,
            )
            await workflow.sleep(interval_seconds)


__all__ = [
    "DEFAULT_SNAPSHOT_INTERVAL_SECONDS",
    "SNAPSHOT_ACTIVITY_TIMEOUT",
    "SnapshotRecord",
    "SnapshotStatus",
    "SnapshotWorkflow",
    "capture_snapshot",
]
