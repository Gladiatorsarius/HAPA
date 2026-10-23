"""Least-privilege Docker container lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import docker
from docker.errors import DockerException


class ContainerExecutionError(RuntimeError):
    """Raised when a container cannot be created or executed."""


@dataclass(frozen=True)
class ContainerResult:
    """Captured result of one container execution."""

    exit_code: int
    stdout: str
    stderr: str


class DockerContainer(Protocol):
    id: str

    def start(self) -> None: ...

    def wait(self, timeout: int | None = None) -> dict[str, Any]: ...

    def logs(self, stdout: bool = True, stderr: bool = True) -> bytes: ...

    def remove(self, force: bool = False) -> None: ...


class DockerClient(Protocol):
    def containers_run(self, **kwargs: Any) -> DockerContainer: ...


class ContainerManager:
    """Run commands in isolated, non-privileged containers."""

    def __init__(
        self,
        client: Any | None = None,
        *,
        image: str = "python:3.14-slim",
        timeout_seconds: int = 300,
        network_mode: str = "none",
        user: str = "65532:65532",
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self.client = client or docker.from_env()
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.network_mode = network_mode
        self.user = user

    def run(
        self,
        command: list[str],
        workspace: str | Path,
        *,
        artifact_dir: str | Path | None = None,
        environment: dict[str, str] | None = None,
    ) -> ContainerResult:
        """Run a bounded command with only the requested workspace mounts."""

        if not command or any(not isinstance(part, str) or not part for part in command):
            raise ValueError("command must contain non-empty strings")
        workspace_path = Path(workspace).expanduser().resolve()
        if not workspace_path.is_dir():
            raise ContainerExecutionError(f"Workspace is not a directory: {workspace_path}")
        volumes: dict[str, dict[str, str]] = {
            str(workspace_path): {"bind": "/workspace", "mode": "rw"},
        }
        if artifact_dir is not None:
            artifact_path = Path(artifact_dir).expanduser().resolve()
            if not artifact_path.is_dir():
                raise ContainerExecutionError(
                    f"Artifact directory is not a directory: {artifact_path}"
                )
            volumes[str(artifact_path)] = {"bind": "/artifacts", "mode": "rw"}

        container: DockerContainer | None = None
        try:
            container = self.client.containers.run(
                self.image,
                command,
                working_dir="/workspace",
                user=self.user,
                volumes=volumes,
                environment=environment or {},
                network_mode=self.network_mode,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"},
                detach=True,
            )
            result = container.wait(timeout=self.timeout_seconds)
            exit_code = int(result["StatusCode"])
            output = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            return ContainerResult(exit_code, output if exit_code == 0 else "", output if exit_code else "")
        except (DockerException, KeyError, TypeError, ValueError) as exc:
            raise ContainerExecutionError("Container execution failed") from exc
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except DockerException as exc:
                    raise ContainerExecutionError("Container cleanup failed") from exc


__all__ = ["ContainerExecutionError", "ContainerManager", "ContainerResult"]
