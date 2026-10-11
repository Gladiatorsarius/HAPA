from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from git import Repo

from src.core.schemas import DiffKind
from src.persistence.git_handler import (
    GitHandlerError,
    GitWorkspaceHandler,
    InvalidWorkspaceError,
    NoWorkspaceChangesError,
)


class GitWorkspaceHandlerTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.repo = Repo.init(self.workspace)
        self._write("tracked.txt", "before\n")
        self.repo.index.add(["tracked.txt"])
        self.repo.index.commit("initial")

    def tearDown(self) -> None:
        if hasattr(self, "handler"):
            self.handler.close()
        self.repo.close()
        self.temp_dir.cleanup()

    def _write(self, relative_path: str, content: str) -> None:
        file_path = self.workspace / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def test_captures_modified_and_untracked_files(self) -> None:
        self._write("tracked.txt", "after\n")
        self._write("new.txt", "new content\n")

        self.handler = GitWorkspaceHandler(self.workspace)
        payload = self.handler.capture_diff()
        changes = {change.path: change for change in payload.files}

        self.assertEqual(changes["tracked.txt"].kind, DiffKind.MODIFIED)
        self.assertEqual(changes["new.txt"].kind, DiffKind.ADDED)
        self.assertTrue(changes["tracked.txt"].patch)
        self.assertEqual(
            len(changes["new.txt"].content_sha256 or ""),
            64,
        )
        self.assertEqual(payload.base_revision, self.repo.head.commit.hexsha)

    def test_captures_deleted_file(self) -> None:
        (self.workspace / "tracked.txt").unlink()

        self.handler = GitWorkspaceHandler(self.workspace)
        payload = self.handler.capture_diff()

        self.assertEqual(payload.files[0].path, "tracked.txt")
        self.assertEqual(payload.files[0].kind, DiffKind.DELETED)
        self.assertIsNone(payload.files[0].content_sha256)
        self.assertTrue(payload.files[0].patch)

    def test_captures_renamed_file(self) -> None:
        (self.workspace / "tracked.txt").rename(self.workspace / "renamed.txt")

        self.handler = GitWorkspaceHandler(self.workspace)
        payload = self.handler.capture_diff()

        self.assertEqual(payload.files[0].kind, DiffKind.RENAMED)
        self.assertEqual(payload.files[0].path, "renamed.txt")
        self.assertEqual(payload.files[0].old_path, "tracked.txt")

    def test_clean_workspace_has_explicit_result(self) -> None:
        with self.assertRaises(NoWorkspaceChangesError):
            self.handler = GitWorkspaceHandler(self.workspace)
            self.handler.capture_diff()

    def test_invalid_workspace_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            with self.assertRaises(InvalidWorkspaceError):
                handler = GitWorkspaceHandler(directory)
                handler.close()

    def test_unknown_revision_is_rejected(self) -> None:
        with self.assertRaisesRegex(GitHandlerError, "Unknown Git revision"):
            self.handler = GitWorkspaceHandler(self.workspace)
            self.handler.capture_diff("missing-revision")
