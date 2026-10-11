from pathlib import Path
from unittest import TestCase

from src.core.settings import AppSettings, load_settings


class SettingsTests(TestCase):
    def test_load_settings_reads_yaml(self) -> None:
        settings = load_settings(Path(__file__).resolve().parents[2] / "config" / "settings.yaml")

        self.assertEqual(settings.name, "HAPA")
        self.assertEqual(settings.environment, "development")
        self.assertEqual(settings.api.host, "0.0.0.0")
        self.assertEqual(settings.api.port, 8000)
        self.assertEqual(settings.temporal.namespace, "hapa")
        self.assertTrue(settings.docker.use_rootless)

    def test_app_settings_requires_name(self) -> None:
        with self.assertRaises(ValueError):
            AppSettings.model_validate({
                "environment": "production",
                "api": {"host": "0.0.0.0", "port": 8000},
                "temporal": {"target": "localhost:7233"},
                "docker": {"socket_url": "unix:///var/run/docker.sock"},
                "browser": {"headless": True},
            })

    def test_load_settings_raises_for_missing_file(self) -> None:
        missing_path = Path(__file__).resolve().parents[2] / "config" / "missing-settings.yaml"

        with self.assertRaises(FileNotFoundError):
            load_settings(missing_path)

    def test_load_settings_rejects_non_mapping_yaml(self) -> None:
        yaml_path = Path(__file__).resolve().parent / "fixtures" / "invalid_settings.yaml"
        yaml_path.parent.mkdir(exist_ok=True)
        yaml_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

        try:
            with self.assertRaises(ValueError):
                AppSettings.from_yaml(yaml_path)
        finally:
            yaml_path.unlink(missing_ok=True)
