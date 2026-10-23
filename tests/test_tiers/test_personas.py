import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.core.schemas import ReviewPersona
from src.tiers.tier3_execution.mode_a_code.multi_persona import (
    EdgeCaseTester,
    PerformanceOptimizer,
    SecurityAuditor,
)
from src.tiers.tier3_execution.mode_a_code.multi_persona._base import PersonaReviewError
from src.tiers.tier3_execution.mode_a_code.runner import CodeRunResult


class FakeRunner:
    def __init__(self, stdout: str, exit_code: int = 0) -> None:
        self.stdout = stdout
        self.exit_code = exit_code
        self.prompt = ""

    def run(self, prompt: str, workspace: str | Path, **kwargs: object) -> CodeRunResult:
        self.prompt = prompt
        return CodeRunResult(("fake",), self.exit_code, self.stdout, "")


class PersonaTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.output = json.dumps(
            [{"title": "Use a safe parser", "description": "Validate input", "severity": 4}]
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_personas_preserve_identity_and_parse_findings(self) -> None:
        for persona_type, persona in (
            (SecurityAuditor, ReviewPersona.SECURITY_AUDITOR),
            (PerformanceOptimizer, ReviewPersona.PERFORMANCE_OPTIMIZER),
            (EdgeCaseTester, ReviewPersona.EDGE_CASE_TESTER),
        ):
            reviewer = persona_type(FakeRunner(self.output))
            findings = reviewer.review("diff --git a/a.py b/a.py", self.workspace)
            self.assertEqual(findings[0].persona, persona)
            self.assertIn(reviewer.focus, reviewer.runner.prompt)

    def test_rejects_malformed_output_and_execution_failure(self) -> None:
        with self.assertRaises(PersonaReviewError):
            SecurityAuditor(FakeRunner("not-json")).review("diff", self.workspace)
        with self.assertRaises(PersonaReviewError):
            SecurityAuditor(FakeRunner("[]", exit_code=1)).review("diff", self.workspace)

    def test_rejects_empty_diff(self) -> None:
        with self.assertRaises(ValueError):
            SecurityAuditor(FakeRunner("[]")).review("", self.workspace)

