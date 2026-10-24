"""Read-only Git workspace diff capture."""

from __future__ import annotations

import difflib
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from git import Repo
from git.exc import BadName, InvalidGitRepositoryError, NoSuchPathError
from git.objects.commit import Commit
from src.core.quality_gates import validate_code_diff
from src.core.schemas import CodeDiffPayload, DiffKind, WorkspaceFileDelta


class GitHandlerError(RuntimeError):
    """Base error for workspace diff capture failures."""


class InvalidWorkspaceError(GitHandlerError):
    """Raised when a path is not a usable Git workspace."""


class NoWorkspaceChangesError(GitHandlerError):
    """Raised when the workspace has no tracked or untracked changes."""


class GitWorkspaceHandler:
    """Capture changes from a Git workspace without mutating the repository."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()
        try:
            self.repository = Repo(self.workspace)
        except (InvalidGitRepositoryError, NoSuchPathError) as error:
            raise InvalidWorkspaceError(
                f"Not a Git repository: {self.workspace}"
            ) from error

    def capture_diff(self, base_revision: str = "HEAD") -> CodeDiffPayload:
        """Capture tracked and untracked changes relative to ``base_revision``."""

        base_commit = self._resolve_revision(base_revision)
        try:
            changes = self._tracked_changes(base_commit.hexsha)
        except (BadName, ValueError, AttributeError) as error:
            raise GitHandlerError(
                f"Unable to inspect workspace changes from {base_revision!r}"
            ) from error

        deltas = [
            self._delta_from_change(change, base_commit.hexsha) for change in changes
        ]
        tracked_paths = {
            path
            for delta in deltas
            for path in (delta.path, delta.old_path)
            if path is not None
        }
        deltas.extend(
            self._delta_from_untracked(path)
            for path in self.repository.untracked_files
            if path not in tracked_paths
        )
        deltas = self._infer_worktree_renames(deltas, base_commit)

        if not deltas:
            raise NoWorkspaceChangesError(
                f"No changes found in workspace: {self.workspace}"
            )

        return validate_code_diff(
            CodeDiffPayload(
                repository=str(self.workspace),
                base_revision=base_commit.hexsha,
                head_revision=self.repository.head.commit.hexsha,
                files=deltas,
                unified_diff=self._combined_patch(deltas),
                generated_at=datetime.now(timezone.utc),
            )
        )

    def close(self) -> None:
        """Release GitPython resources held by this handler."""

        self.repository.close()

    def __enter__(self) -> GitWorkspaceHandler:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _resolve_revision(self, revision: str) -> Commit:
        try:
            return self.repository.commit(revision)
        except (BadName, ValueError) as error:
            raise GitHandlerError(f"Unknown Git revision: {revision!r}") from error

    def _tracked_changes(self, base_revision: str) -> list[tuple[str, str, str | None]]:
        output = self.repository.git.diff(
            base_revision,
            "--name-status",
            "-M",
            "-z",
            "--",
        )
        fields = output.split("\x00")
        changes: list[tuple[str, str, str | None]] = []
        index = 0
        while index < len(fields) and fields[index]:
            status = fields[index]
            index += 1
            change_type = status[0]
            if change_type == "R":
                if index + 1 >= len(fields):
                    raise GitHandlerError("Git returned an incomplete rename record")
                old_path, new_path = fields[index : index + 2]
                index += 2
                changes.append((change_type, new_path, old_path))
            else:
                if index >= len(fields):
                    raise GitHandlerError("Git returned an incomplete change record")
                changes.append((change_type, fields[index], None))
                index += 1
        return changes

    def _delta_from_change(
        self,
        change: tuple[str, str, str | None],
        base_revision: str,
    ) -> WorkspaceFileDelta:
        change_type, path_value, old_path_value = change
        if change_type == "R":
            path = self._relative_path(path_value)
            old_path = self._relative_path(old_path_value)
            kind = DiffKind.RENAMED
        elif change_type == "A":
            path = self._relative_path(path_value)
            old_path = None
            kind = DiffKind.ADDED
        elif change_type == "D":
            path = self._relative_path(path_value)
            old_path = None
            kind = DiffKind.DELETED
        else:
            path = self._relative_path(path_value)
            old_path = None
            kind = DiffKind.MODIFIED

        patch = self._tracked_patch(base_revision, path, old_path)
        if kind in {DiffKind.ADDED, DiffKind.MODIFIED, DiffKind.DELETED} and not patch:
            patch = "Binary files differ"

        return WorkspaceFileDelta(
            path=path,
            kind=kind,
            patch=patch or None,
            old_path=old_path,
            content_sha256=self._content_hash(path),
        )

    def _tracked_patch(
        self,
        base_revision: str,
        path: str,
        old_path: str | None,
    ) -> str:
        paths = [old_path, path] if old_path is not None else [path]
        patch = self.repository.git.diff(
            base_revision,
            "--binary",
            "-M",
            "--",
            *paths,
        )
        return self._decode_patch(patch)

    def _delta_from_untracked(self, path: str) -> WorkspaceFileDelta:
        relative_path = self._relative_path(path)
        file_path = self.workspace / Path(path)
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8", errors="replace")
            patch = "".join(
                difflib.unified_diff(
                    [],
                    content.splitlines(keepends=True),
                    fromfile="/dev/null",
                    tofile=relative_path,
                )
            )
        else:
            patch = f"Untracked path: {relative_path}"

        return WorkspaceFileDelta(
            path=relative_path,
            kind=DiffKind.ADDED,
            patch=patch or "Binary files differ",
            content_sha256=self._content_hash(relative_path),
        )

    def _relative_path(self, path: str | None) -> str:
        if not path:
            raise GitHandlerError("Git returned a change without a file path")
        return Path(path).as_posix()

    def _content_hash(self, relative_path: str) -> str | None:
        file_path = self.workspace / Path(relative_path)
        if not file_path.is_file():
            return None
        digest = hashlib.sha256()
        with file_path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _infer_worktree_renames(
        self,
        deltas: list[WorkspaceFileDelta],
        base_commit: Commit,
    ) -> list[WorkspaceFileDelta]:
        added = [
            delta
            for delta in deltas
            if delta.kind == DiffKind.ADDED and delta.content_sha256
        ]
        consumed: set[str] = set()
        result: list[WorkspaceFileDelta] = []
        for delta in deltas:
            if delta.kind != DiffKind.DELETED:
                if delta.path not in consumed:
                    result.append(delta)
                continue
            old_hash = self._revision_content_hash(base_commit, delta.path)
            match = next(
                (
                    candidate
                    for candidate in added
                    if candidate.path not in consumed
                    and candidate.content_sha256 == old_hash
                ),
                None,
            )
            if match is None:
                result.append(delta)
                continue
            consumed.add(match.path)
            result.append(
                match.model_copy(
                    update={
                        "kind": DiffKind.RENAMED,
                        "old_path": delta.path,
                    }
                )
            )
        return result

    @staticmethod
    def _revision_content_hash(commit: Commit, relative_path: str) -> str | None:
        try:
            blob = commit.tree / Path(relative_path).as_posix()
        except (KeyError, AttributeError):
            return None
        return hashlib.sha256(blob.data_stream.read()).hexdigest()

    @staticmethod
    def _decode_patch(patch: bytes | str | None) -> str:
        if patch is None:
            return ""
        if isinstance(patch, bytes):
            return patch.decode("utf-8", errors="replace")
        return patch

    @staticmethod
    def _combined_patch(deltas: list[WorkspaceFileDelta]) -> str | None:
        patches = [delta.patch for delta in deltas if delta.patch]
        return "\n".join(patches) or None


__all__ = [
    "GitHandlerError",
    "GitWorkspaceHandler",
    "InvalidWorkspaceError",
    "NoWorkspaceChangesError",
]
