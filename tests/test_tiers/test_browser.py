from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

from src.tiers.tier3_execution.mode_b_docker.visual.browser import BrowserAutomation


class BrowserAutomationTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.page = Mock()
        self.browser = Mock()
        self.browser.new_page.return_value = self.page
        self.playwright = Mock()
        self.playwright.chromium.launch.return_value = self.browser
        self.factory = Mock(return_value=Mock(start=Mock(return_value=self.playwright)))
        self.automation = BrowserAutomation(
            screenshot_dir=Path(self.temp_dir.name) / "screenshots",
            playwright_factory=self.factory,
        )

    def tearDown(self) -> None:
        self.automation.close()
        self.temp_dir.cleanup()

    def test_runs_navigation_actions_and_screenshot(self) -> None:
        self.automation.start()
        self.automation.navigate("https://example.test")
        self.automation.fill("#name", "HAPA")
        self.automation.click("button")
        destination = self.automation.screenshot("home.png")

        self.assertEqual(destination.name, "home.png")
        self.page.goto.assert_called_once()
        self.page.locator.assert_any_call("#name")
        self.page.screenshot.assert_called_once()

    def test_rejects_nested_screenshot_name(self) -> None:
        with self.assertRaises(ValueError):
            self.automation.screenshot("../secret.png")

    def test_context_manager_closes_resources(self) -> None:
        with self.automation:
            self.assertIsNotNone(self.automation.page)
        self.browser.close.assert_called_once()
        self.playwright.stop.assert_called_once()

