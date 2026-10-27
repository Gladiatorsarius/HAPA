"""Validation helpers for structured artifacts crossing phase boundaries."""

from __future__ import annotations

import json
from typing import Any

from .schemas import CodeDiffPayload, TestReport


def validate_code_diff(payload: CodeDiffPayload | dict[str, Any]) -> CodeDiffPayload:
    """Return a JSON-round-tripped diff payload or raise a validation error."""

    source = (
        payload.model_dump_json()
        if isinstance(payload, CodeDiffPayload)
        else json.dumps(payload)
    )
    return CodeDiffPayload.model_validate_json(source)


def validate_test_report(report: TestReport | dict[str, Any]) -> TestReport:
    """Return a JSON-round-tripped test report or raise a validation error."""

    source = (
        report.model_dump_json()
        if isinstance(report, TestReport)
        else json.dumps(report)
    )
    return TestReport.model_validate_json(source)


__all__ = ["validate_code_diff", "validate_test_report"]
