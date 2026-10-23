"""OpenCV-based visual parsing primitives."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2


class VisionParserError(RuntimeError):
    """Raised when an image cannot be loaded or parsed."""


@dataclass(frozen=True)
class ImageDetection:
    """Bounding-box detection in image pixel coordinates."""

    x: int
    y: int
    width: int
    height: int
    confidence: float
    label: str


class VisionParser:
    """Parse high-contrast regions from screenshots."""

    def __init__(self, threshold: int = 128, minimum_area: int = 1) -> None:
        if not 0 <= threshold <= 255:
            raise ValueError("threshold must be between 0 and 255")
        if minimum_area <= 0:
            raise ValueError("minimum_area must be greater than zero")
        self.threshold = threshold
        self.minimum_area = minimum_area

    def detect_regions(self, image_path: str | Path) -> list[ImageDetection]:
        path = Path(image_path).expanduser().resolve()
        if not path.is_file():
            raise VisionParserError(f"Image file not found: {path}")
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise VisionParserError(f"Unable to read image: {path}")
        _ignored, binary = cv2.threshold(image, self.threshold, 255, cv2.THRESH_BINARY)
        contours, _hierarchy = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.minimum_area:
                continue
            x, y, width, height = cv2.boundingRect(contour)
            detections.append(
                ImageDetection(x, y, width, height, min(1.0, area / max(width * height, 1)), "region")
            )
        return sorted(detections, key=lambda detection: (detection.y, detection.x))


__all__ = ["ImageDetection", "VisionParser", "VisionParserError"]
