import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from git import Repo

from src.persistence.temporal_workflows.snapshot_wf import (
    DEFAULT_SNAPSHOT_INTERVAL_SECONDS,
    SnapshotStatus,
    capture_snapshot,
)


class SnapshotWorkflowActivityTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name) / "workspace"
        self.snapshot_dir = Path(self.temp_dir.name) / "persistent-volume" / "checkpoints"
        self.workspace.mkdir()
        self.repo = Repo.init(self.workspace)
        self._write("tracked.txt", "before\n")
        self.repo.index.add(["tracked.txt"])
        self.repo.index.commit("initial")

    def tearDown(self) -> None:
        self.repo.close()
        self.temp_dir.cleanup()

    def _write(self, relative_path: str, content: str) -> None:
        file_path = self.workspace / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def test_captures_and_atomically_persists_checkpoint(self) -> None:
        self._write("tracked.txt", "after\n")

        result = asyncio.run(
            capture_snapshot(
                str(self.workspace),
                str(self.snapshot_dir),
            )
        )

        checkpoint_path = Path(result["path"])
        self.assertEqual(result["status"], SnapshotStatus.CAPTURED.value)
        self.assertTrue(checkpoint_path.is_file())
        self.assertEqual(list(self.snapshot_dir.glob("*.tmp")), [])
        record = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        self.assertEqual(record["status"], SnapshotStatus.CAPTURED.value)
        self.assertEqual(record["diff"]["files"][0]["path"], "tracked.txt")

    def test_persists_explicit_no_changes_result(self) -> None:
        result = asyncio.run(
            capture_snapshot(
                str(self.workspace),
                str(self.snapshot_dir),
            )
        )

        record = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], SnapshotStatus.NO_CHANGES.value)
        self.assertEqual(record["status"], SnapshotStatus.NO_CHANGES.value)
        self.assertIsNone(record["diff"])

    def test_uses_five_second_default_cadence(self) -> None:
        self.assertEqual(DEFAULT_SNAPSHOT_INTERVAL_SECONDS, 5)
