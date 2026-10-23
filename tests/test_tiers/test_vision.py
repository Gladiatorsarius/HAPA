from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import cv2
import numpy as np

from src.tiers.tier3_execution.mode_b_docker.visual.vision import (
    VisionParser,
    VisionParserError,
)


class VisionParserTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.image_path = Path(self.temp_dir.name) / "image.png"
        image = np.zeros((20, 30), dtype=np.uint8)
        image[2:8, 3:10] = 255
        self.assertTrue(cv2.imwrite(str(self.image_path), image))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_detects_regions_deterministically(self) -> None:
        detections = VisionParser().detect_regions(self.image_path)
        self.assertEqual(len(detections), 1)
        self.assertEqual((detections[0].x, detections[0].y), (3, 2))
        self.assertEqual((detections[0].width, detections[0].height), (7, 6))

    def test_rejects_missing_and_unreadable_images(self) -> None:
        with self.assertRaises(VisionParserError):
            VisionParser().detect_regions(self.image_path.parent / "missing.png")
        bad = Path(self.temp_dir.name) / "bad.png"
        bad.write_text("not an image", encoding="utf-8")
        with self.assertRaises(VisionParserError):
            VisionParser().detect_regions(bad)

    def test_validates_parameters(self) -> None:
        with self.assertRaises(ValueError):
            VisionParser(threshold=256)
        with self.assertRaises(ValueError):
            VisionParser(minimum_area=0)

