"""Claude Code CLI execution wrapper."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class CodeRunnerError(RuntimeError):
    """Raised when the CLI cannot be executed."""


@dataclass(frozen=True)
class CodeRunResult:
    """Structured result from one CLI invocation."""

    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class ClaudeCodeRunner:
    """Run Claude Code in a validated isolated workspace."""

    def __init__(self, executable: str = "claude", timeout_seconds: int = 600) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def build_command(self, prompt: str) -> tuple[str, ...]:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        return (self.executable, "--print", prompt)

    def run(
        self,
        prompt: str,
        workspace: str | Path,
        *,
        timeout_seconds: int | None = None,
        environment: dict[str, str] | None = None,
    ) -> CodeRunResult:
        workspace_path = Path(workspace).expanduser().resolve()
        if not workspace_path.is_dir():
            raise CodeRunnerError(f"Workspace is not a directory: {workspace_path}")
        if shutil.which(self.executable) is None:
            raise CodeRunnerError(f"Claude Code executable not found: {self.executable}")
        command = self.build_command(prompt)
        timeout = timeout_seconds if timeout_seconds is not None else self.timeout_seconds
        if timeout <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        try:
            completed = subprocess.run(
                command,
                cwd=workspace_path,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CodeRunResult(
                command,
                -1,
                (exc.stdout or "") if isinstance(exc.stdout, str) else "",
                (exc.stderr or "") if isinstance(exc.stderr, str) else "",
                timed_out=True,
            )
        except OSError as exc:
            raise CodeRunnerError(f"Unable to execute Claude Code: {self.executable}") from exc
        return CodeRunResult(
            command,
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )


__all__ = ["ClaudeCodeRunner", "CodeRunResult", "CodeRunnerError"]
