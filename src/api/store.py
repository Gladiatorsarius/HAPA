"""Durable SQLite-backed state used by the API process."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import UUID


class ApiStore:
    def __init__(self, database_url: str) -> None:
        if not database_url.startswith("sqlite:///"):
            raise ValueError("Phase 4 currently supports sqlite:/// database URLs")
        self.path = Path(database_url.removeprefix("sqlite:///"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, payload TEXT NOT NULL, state TEXT NOT NULL,
                approval_required INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, state TEXT NOT NULL,
                created_at TEXT NOT NULL, decided_at TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_task(self, task: dict[str, Any], state: str, approval_required: bool) -> dict[str, Any]:
        now = self._now()
        task_id = str(task["task_id"])
        with self._lock:
            self._connection.execute(
                "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, json.dumps(task, default=str), state, int(approval_required), now, now),
            )
            self._connection.commit()
        return self.get_task(UUID(task_id))

    def update_task(self, task_id: UUID, *, state: str, approval_required: bool | None = None) -> dict[str, Any]:
        now = self._now()
        with self._lock:
            if approval_required is None:
                self._connection.execute("UPDATE tasks SET state=?, updated_at=? WHERE task_id=?", (state, now, str(task_id)))
            else:
                self._connection.execute(
                    "UPDATE tasks SET state=?, approval_required=?, updated_at=? WHERE task_id=?",
                    (state, int(approval_required), now, str(task_id)),
                )
            self._connection.commit()
        return self.get_task(task_id)

    def get_task(self, task_id: UUID) -> dict[str, Any]:
        row = self._connection.execute("SELECT * FROM tasks WHERE task_id=?", (str(task_id),)).fetchone()
        if row is None:
            raise KeyError(str(task_id))
        result = json.loads(row["payload"])
        result.update(state=row["state"], approval_required=bool(row["approval_required"]), created_at=row["created_at"], updated_at=row["updated_at"])
        return result

    def list_tasks(self, active_only: bool = False) -> list[dict[str, Any]]:
        query = "SELECT task_id FROM tasks"
        if active_only:
            query += " WHERE state IN ('PENDING', 'RUNNING', 'BLOCKED_AT_HUMAN_GATE')"
        return [self.get_task(UUID(row["task_id"])) for row in self._connection.execute(query).fetchall()]

    def add_approval(self, task_id: UUID, approval_id: UUID) -> None:
        now = self._now()
        with self._lock:
            self._connection.execute("INSERT INTO approvals VALUES (?, ?, 'PENDING', ?, NULL)", (str(approval_id), str(task_id), now))
            self._connection.commit()

    def list_approvals(self, pending_only: bool = True) -> list[dict[str, Any]]:
        query = "SELECT * FROM approvals" + (" WHERE state='PENDING'" if pending_only else "")
        return [dict(row) for row in self._connection.execute(query).fetchall()]

    def decide_approval(self, approval_id: UUID, state: str) -> dict[str, Any]:
        with self._lock:
            cursor = self._connection.execute(
                "UPDATE approvals SET state=?, decided_at=? WHERE approval_id=? AND state='PENDING'",
                (state, self._now(), str(approval_id)),
            )
            if cursor.rowcount != 1:
                raise KeyError(str(approval_id))
            self._connection.commit()
        row = self._connection.execute("SELECT * FROM approvals WHERE approval_id=?", (str(approval_id),)).fetchone()
        return dict(row)

    def add_event(self, task_id: UUID, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        now = self._now()
        with self._lock:
            cursor = self._connection.execute(
                "INSERT INTO events (task_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
                (str(task_id), event_type, json.dumps(payload, default=str), now),
            )
            self._connection.commit()
        return {"event_id": cursor.lastrowid, "task_id": str(task_id), "event_type": event_type, "payload": payload, "created_at": now}

    def list_events(self, task_id: UUID) -> list[dict[str, Any]]:
        rows = self._connection.execute("SELECT * FROM events WHERE task_id=? ORDER BY event_id", (str(task_id),)).fetchall()
        return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]
