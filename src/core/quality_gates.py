"""Validation helpers for structured artifacts crossing phase boundaries."""

from __future__ import annotations

import json
from typing import Any

from .schemas import CodeDiffPayload, TestReport


def validate_code_diff(payload: CodeDiffPayload | dict[str, Any]) -> CodeDiffPayload:
    """Return a JSON-round-tripped diff payload or raise a validation error."""

    diff = (
        payload
        if isinstance(payload, CodeDiffPayload)
        else CodeDiffPayload.model_validate_json(json.dumps(payload))
    )
    return CodeDiffPayload.model_validate_json(diff.model_dump_json())


def validate_test_report(report: TestReport | dict[str, Any]) -> TestReport:
    """Return a JSON-round-tripped test report or raise a validation error."""

    structured = (
        report
        if isinstance(report, TestReport)
        else TestReport.model_validate_json(json.dumps(report))
    )
    return TestReport.model_validate_json(structured.model_dump_json())


__all__ = ["validate_code_diff", "validate_test_report"]
