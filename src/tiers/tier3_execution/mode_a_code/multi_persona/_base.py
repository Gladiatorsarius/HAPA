"""Shared implementation for structured review personas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from src.core.schemas import ReviewFinding, ReviewPersona
from src.tiers.tier3_execution.mode_a_code.runner import ClaudeCodeRunner, CodeRunResult


class PersonaReviewError(RuntimeError):
    """Raised when a persona cannot produce valid structured findings."""


class Runner(Protocol):
    def run(self, prompt: str, workspace: str | Path, **kwargs: object) -> CodeRunResult: ...


class PersonaReviewer:
    persona: ReviewPersona
    focus: str

    def __init__(self, runner: Runner | None = None) -> None:
        self.runner = runner or ClaudeCodeRunner()

    def build_prompt(self, diff: str) -> str:
        if not diff.strip():
            raise ValueError("diff must not be empty")
        return (
            f"Review this code diff as a {self.focus}. "
            "Return only a JSON array of findings with title, description, severity, "
            "file_path, line_start, line_end, recommendation, and blocking fields.\n\n"
            + diff
        )

    def review(self, diff: str, workspace: str | Path) -> list[ReviewFinding]:
        result = self.runner.run(self.build_prompt(diff), workspace)
        if result.timed_out or result.exit_code != 0:
            raise PersonaReviewError(
                f"{self.persona.value} review execution failed with exit code {result.exit_code}"
            )
        try:
            payload = json.loads(result.stdout)
            if not isinstance(payload, list):
                raise ValueError("review output must be an array")
            return [
                ReviewFinding.model_validate({**item, "persona": self.persona})
                for item in payload
            ]
        except (TypeError, ValueError) as exc:
            raise PersonaReviewError(
                f"{self.persona.value} returned invalid structured findings"
            ) from exc


__all__ = ["PersonaReviewError", "PersonaReviewer"]
