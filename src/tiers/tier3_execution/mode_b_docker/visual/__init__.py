"""Visual execution adapters."""

from .browser import BrowserAutomation, BrowserAutomationError
from .vision import ImageDetection, VisionParser, VisionParserError

__all__ = [
    "BrowserAutomation",
    "BrowserAutomationError",
    "ImageDetection",
    "VisionParser",
    "VisionParserError",
]
