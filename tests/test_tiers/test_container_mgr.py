from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

from src.tiers.tier3_execution.mode_b_docker.container_mgr import (
    ContainerManager,
    ContainerResult,
)


class ContainerManagerTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name) / "workspace"
        self.artifacts = Path(self.temp_dir.name) / "artifacts"
        self.workspace.mkdir()
        self.artifacts.mkdir()
        self.container = Mock()
        self.container.wait.return_value = {"StatusCode": 0}
        self.container.logs.return_value = b"ok\n"
        self.client = Mock()
        self.client.containers.run.return_value = self.container
        self.manager = ContainerManager(self.client)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_runs_with_least_privilege_and_scoped_mounts(self) -> None:
        result = self.manager.run(["python", "-c", "print('ok')"], self.workspace, artifact_dir=self.artifacts)

        self.assertEqual(result, ContainerResult(0, "ok\n", ""))
        options = self.client.containers.run.call_args.kwargs
        self.assertEqual(options["user"], "65532:65532")
        self.assertEqual(options["network_mode"], "none")
        self.assertEqual(options["cap_drop"], ["ALL"])
        self.assertEqual(options["security_opt"], ["no-new-privileges:true"])
        self.assertTrue(options["read_only"])
        self.assertEqual(options["volumes"][str(self.workspace.resolve())]["mode"], "rw")
        self.assertNotIn(str(Path.home()), options["volumes"])
        self.container.remove.assert_called_once_with(force=True)

    def test_nonzero_exit_is_returned_and_output_is_stderr(self) -> None:
        self.container.wait.return_value = {"StatusCode": 2}
        self.container.logs.return_value = b"failed\n"

        result = self.manager.run(["false"], self.workspace)

        self.assertEqual(result.exit_code, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "failed\n")

    def test_rejects_invalid_workspace_and_command(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.run([], self.workspace)
        with self.assertRaisesRegex(RuntimeError, "not a directory"):
            self.manager.run(["true"], self.workspace / "missing")

