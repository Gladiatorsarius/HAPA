from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from git import Repo

from src.tiers.tier3_execution.mode_b_docker.workspace import (
    WorkspaceIsolationError,
    WorkspaceManager,
)


class WorkspaceManagerTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repository = self.root / "repository"
        self.repository.mkdir()
        self.repo = Repo.init(self.repository)
        (self.repository / "tracked.txt").write_text("base\n", encoding="utf-8")
        self.repo.index.add(["tracked.txt"])
        self.commit = self.repo.index.commit("initial")
        self.manager = WorkspaceManager(self.repository, self.root / "isolated")

    def tearDown(self) -> None:
        self.manager.close()
        self.repo.close()
        self.temp_dir.cleanup()

    def test_creates_independent_worktree(self) -> None:
        workspace = self.manager.create(self.commit.hexsha, name="task-1")
        try:
            self.assertTrue((workspace.path / ".git").exists())
            (workspace.path / "tracked.txt").write_text("changed\n", encoding="utf-8")
            self.assertEqual(
                (self.repository / "tracked.txt").read_text(encoding="utf-8"),
                "base\n",
            )
        finally:
            workspace.cleanup()
        self.assertFalse((self.root / "isolated" / "task-1").exists())

    def test_rejects_unknown_revision(self) -> None:
        with self.assertRaises(WorkspaceIsolationError):
            self.manager.create("not-a-revision")

    def test_rejects_path_traversal_and_duplicate_names(self) -> None:
        with self.assertRaises(WorkspaceIsolationError):
            self.manager.create(name="../outside")
        workspace = self.manager.create(name="duplicate")
        try:
            with self.assertRaises(WorkspaceIsolationError):
                self.manager.create(name="duplicate")
        finally:
            workspace.cleanup()

    def test_context_manager_cleans_up(self) -> None:
        with self.manager.create() as workspace:
            path = workspace.path
            self.assertTrue(path.exists())
        self.assertFalse(path.exists())

