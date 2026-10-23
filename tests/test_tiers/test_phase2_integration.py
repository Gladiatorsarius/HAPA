from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from git import Repo

from src.tiers.tier3_execution.mode_a_code.runner import ClaudeCodeRunner
from src.tiers.tier3_execution.mode_b_docker.visual.vision import VisionParser
from src.tiers.tier3_execution.mode_b_docker.workspace import WorkspaceManager


class Phase2IntegrationTests(TestCase):
    def test_isolated_workspace_can_feed_execution_and_visual_artifacts(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            repo = Repo.init(repository)
            (repository / "task.txt").write_text("base\n", encoding="utf-8")
            repo.index.add(["task.txt"])
            commit = repo.index.commit("initial")
            manager = WorkspaceManager(repository, root / "workspaces")
            try:
                with manager.create(commit.hexsha) as workspace:
                    (workspace.path / "task.txt").write_text("changed\n", encoding="utf-8")
                    result = ClaudeCodeRunner(executable="/bin/echo").run(
                        "validate the task",
                        workspace.path,
                    )
                    self.assertEqual(result.exit_code, 0)
                    self.assertIn("--print", result.stdout)
                    image = root / "screenshot.png"
                    import cv2
                    import numpy as np

                    pixels = np.zeros((10, 10), dtype=np.uint8)
                    pixels[1:4, 1:4] = 255
                    self.assertTrue(cv2.imwrite(str(image), pixels))
                    self.assertEqual(len(VisionParser().detect_regions(image)), 1)
            finally:
                manager.close()
                repo.close()
