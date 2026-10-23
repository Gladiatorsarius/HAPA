"""Playwright browser automation bindings."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


class BrowserAutomationError(RuntimeError):
    """Raised when browser automation fails."""


class BrowserAutomation:
    """Manage one bounded Playwright browser session."""

    def __init__(
        self,
        *,
        headless: bool = True,
        screenshot_dir: str | Path = "artifacts/screenshots",
        playwright_factory: Callable[[], Any] = sync_playwright,
    ) -> None:
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir).expanduser().resolve()
        self._playwright_factory = playwright_factory
        self._playwright: Any | None = None
        self._browser: Any | None = None
        self.page: Any | None = None

    def start(self) -> None:
        if self.page is not None:
            return
        try:
            self._playwright = self._playwright_factory().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self.page = self._browser.new_page()
        except PlaywrightError as exc:
            self.close()
            raise BrowserAutomationError("Unable to start Playwright browser") from exc

    def navigate(self, url: str, *, timeout_ms: int = 30_000) -> None:
        page = self._require_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        except PlaywrightError as exc:
            raise BrowserAutomationError(f"Unable to navigate to {url}") from exc

    def click(self, selector: str, *, timeout_ms: int = 30_000) -> None:
        try:
            self._require_page().locator(selector).click(timeout=timeout_ms)
        except PlaywrightError as exc:
            raise BrowserAutomationError(f"Unable to click selector: {selector}") from exc

    def fill(self, selector: str, value: str, *, timeout_ms: int = 30_000) -> None:
        try:
            self._require_page().locator(selector).fill(value, timeout=timeout_ms)
        except PlaywrightError as exc:
            raise BrowserAutomationError(f"Unable to fill selector: {selector}") from exc

    def screenshot(self, name: str) -> Path:
        if not name or Path(name).name != name:
            raise ValueError("screenshot name must be a file name")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        destination = self.screenshot_dir / name
        try:
            self._require_page().screenshot(path=str(destination), full_page=True)
        except PlaywrightError as exc:
            raise BrowserAutomationError("Unable to capture screenshot") from exc
        return destination

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        self.page = None
        self._browser = None
        self._playwright = None

    def __enter__(self) -> BrowserAutomation:
        self.start()
        return self

    def __exit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        self.close()

    def _require_page(self) -> Any:
        if self.page is None:
            raise BrowserAutomationError("Browser session has not been started")
        return self.page


__all__ = ["BrowserAutomation", "BrowserAutomationError"]
