import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase


ENTRYPOINT = Path(__file__).parents[1] / "scripts" / "entrypoint.sh"


class EntrypointContractTests(TestCase):
    def test_declares_default_command_and_exec_passthrough(self) -> None:
        script = ENTRYPOINT.read_text(encoding="utf-8")

        self.assertIn('if [ "$#" -gt 0 ]; then', script)
        self.assertIn('exec "$@"', script)
        self.assertIn("exec uvicorn src.main:app", script)


class EntrypointShellTests(TestCase):
    def setUp(self) -> None:
        self.bash = shutil.which("bash")
        if self.bash is None or subprocess.run(
            [self.bash, "-c", "exit 0"],
            check=False,
            capture_output=True,
        ).returncode != 0:
            self.skipTest("bash is required to exercise the POSIX entrypoint")

    def run_entrypoint(
        self,
        *arguments: str,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        process_environment = os.environ.copy()
        if environment is not None:
            process_environment.update(environment)
        return subprocess.run(
            [self.bash, "./scripts/entrypoint.sh", *arguments],
            check=False,
            capture_output=True,
            text=True,
            env=process_environment,
            cwd=ENTRYPOINT.parents[1],
        )

    def test_explicit_command_creates_runtime_directories_and_preserves_arguments(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            workspace = root / "workspace"
            snapshots = root / "checkpoints"
            screenshots = root / "screenshots"

            result = self.run_entrypoint(
                "printf",
                "%s|%s",
                "first argument",
                environment={
                    "HAPA_WORKSPACE_ROOT": str(workspace),
                    "HAPA_SNAPSHOT_DIR": str(snapshots),
                    "HAPA_SCREENSHOT_DIR": str(screenshots),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "first argument|%s")
            self.assertTrue(workspace.is_dir())
            self.assertTrue(snapshots.is_dir())
            self.assertTrue(screenshots.is_dir())

    def test_default_command_executes_uvicorn_with_api_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            arguments_file = root / "uvicorn-arguments.txt"
            fake_uvicorn = fake_bin / "uvicorn"
            fake_uvicorn.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$HAPA_TEST_ARGUMENTS_FILE\"\n",
                encoding="utf-8",
            )
            fake_uvicorn.chmod(0o755)

            result = self.run_entrypoint(
                environment={
                    "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
                    "HAPA_TEST_ARGUMENTS_FILE": str(arguments_file),
                    "HAPA_WORKSPACE_ROOT": str(root / "workspace"),
                    "HAPA_SNAPSHOT_DIR": str(root / "checkpoints"),
                    "HAPA_SCREENSHOT_DIR": str(root / "screenshots"),
                    "HAPA_API_HOST": "127.0.0.1",
                    "HAPA_API_PORT": "8123",
                    "HAPA_API_LOG_LEVEL": "debug",
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                arguments_file.read_text(encoding="utf-8").splitlines(),
                [
                    "src.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8123",
                    "--log-level",
                    "debug",
                ],
            )

    def test_rejects_invalid_api_port(self) -> None:
        result = self.run_entrypoint(environment={"HAPA_API_PORT": "not-a-port"})

        self.assertEqual(result.returncode, 2)
        self.assertIn("HAPA_API_PORT must be a positive integer", result.stderr)
