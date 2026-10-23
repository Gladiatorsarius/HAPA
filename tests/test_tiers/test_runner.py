from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.tiers.tier3_execution.mode_a_code.runner import (
    ClaudeCodeRunner,
    CodeRunnerError,
)


class ClaudeCodeRunnerTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_builds_noninteractive_command(self) -> None:
        runner = ClaudeCodeRunner(executable="/usr/local/bin/claude")
        self.assertEqual(
            runner.build_command("inspect the repository"),
            ("/usr/local/bin/claude", "--print", "inspect the repository"),
        )

    @patch("src.tiers.tier3_execution.mode_a_code.runner.shutil.which", return_value="/bin/echo")
    def test_captures_success(self, _which: object) -> None:
        runner = ClaudeCodeRunner(executable="/bin/echo")
        result = runner.run("hello", self.workspace)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stderr, "")
        self.assertFalse(result.timed_out)

    @patch("src.tiers.tier3_execution.mode_a_code.runner.shutil.which", return_value=None)
    def test_reports_missing_cli(self, _which: object) -> None:
        with self.assertRaisesRegex(CodeRunnerError, "not found"):
            ClaudeCodeRunner().run("hello", self.workspace)

    def test_reports_invalid_workspace(self) -> None:
        with self.assertRaisesRegex(CodeRunnerError, "not a directory"):
            ClaudeCodeRunner(executable="/bin/echo").run("hello", self.workspace / "missing")

    @patch("src.tiers.tier3_execution.mode_a_code.runner.shutil.which", return_value="/bin/echo")
    @patch("src.tiers.tier3_execution.mode_a_code.runner.subprocess.run")
    def test_timeout_is_structured(self, run: object, _which: object) -> None:
        from subprocess import TimeoutExpired

        run.side_effect = TimeoutExpired(["claude"], 1)
        result = ClaudeCodeRunner().run("hello", self.workspace)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.exit_code, -1)
