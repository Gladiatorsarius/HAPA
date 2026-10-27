"""Isolated Git workspaces for Tier 3 execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from gitdb.exc import BadName


class WorkspaceIsolationError(RuntimeError):
    """Raised when an isolated workspace cannot be created or managed."""


@dataclass
class IsolatedWorkspace:
    """A Git worktree that can be independently modified and removed."""

    path: Path
    repository: Path
    manager: WorkspaceManager
    _cleaned: bool = False

    def cleanup(self) -> None:
        """Remove this worktree and its directory."""

        if not self._cleaned:
            self.manager.remove(self)

    def __enter__(self) -> IsolatedWorkspace:
        return self

    def __exit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        self.cleanup()


class WorkspaceManager:
    """Create and clean up copy-on-write Git worktrees."""

    def __init__(self, repository: str | Path, workspace_root: str | Path | None = None) -> None:
        self.repository = Path(repository).expanduser().resolve()
        try:
            self._repo = Repo(self.repository)
        except (InvalidGitRepositoryError, GitCommandError) as exc:
            raise WorkspaceIsolationError(
                f"Not a valid Git repository: {self.repository}"
            ) from exc
        if self._repo.bare:
            raise WorkspaceIsolationError("Bare repositories are not supported")
        self.workspace_root = (
            Path(workspace_root).expanduser().resolve()
            if workspace_root is not None
            else self.repository.parent / ".hapa-workspaces"
        )
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def create(self, base_revision: str = "HEAD", name: str | None = None) -> IsolatedWorkspace:
        """Create a detached worktree from a validated revision."""

        try:
            self._repo.commit(base_revision)
        except (BadName, ValueError, GitCommandError) as exc:
            raise WorkspaceIsolationError(
                f"Unknown Git revision: {base_revision}"
            ) from exc

        workspace_path = self._allocate_path(name)
        try:
            self._repo.git.worktree("add", "--detach", str(workspace_path), base_revision)
        except GitCommandError as exc:
            workspace_path.rmdir() if workspace_path.exists() else None
            raise WorkspaceIsolationError(
                f"Unable to create isolated workspace at {workspace_path}"
            ) from exc
        return IsolatedWorkspace(workspace_path, self.repository, self)

    def remove(self, workspace: IsolatedWorkspace) -> None:
        """Remove a worktree only when it belongs to this manager."""

        path = workspace.path.resolve()
        if workspace.manager is not self or not self._within_root(path):
            raise WorkspaceIsolationError("Workspace does not belong to this manager")
        try:
            self._repo.git.worktree("remove", "--force", str(path))
        except GitCommandError as exc:
            raise WorkspaceIsolationError(f"Unable to remove workspace: {path}") from exc
        workspace._cleaned = True

    def close(self) -> None:
        self._repo.close()

    def _allocate_path(self, name: str | None) -> Path:
        if name is not None:
            candidate = (self.workspace_root / name).resolve()
            if not self._within_root(candidate) or candidate == self.workspace_root:
                raise WorkspaceIsolationError("Workspace name escapes workspace root")
            if candidate.exists():
                raise WorkspaceIsolationError(f"Workspace already exists: {candidate}")
            candidate.mkdir(parents=True)
            return candidate
        return Path(mkdtemp(prefix="workspace-", dir=self.workspace_root))

    def _within_root(self, path: Path) -> bool:
        return path.is_relative_to(self.workspace_root)


__all__ = ["IsolatedWorkspace", "WorkspaceIsolationError", "WorkspaceManager"]
