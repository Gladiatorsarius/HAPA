import tempfile
from unittest import TestCase

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.core.settings import AppSettings


class RouteTests(TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.settings = AppSettings.model_validate({
            "name": "test",
            "llm": {"strong_model": "strong", "tier3_models": ["small"]},
            "storage": {"database_url": f"sqlite:///{self.directory.name}/hapa.db"},
        })
        self.client = TestClient(create_app(self.settings))

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_health_is_public_and_task_routes_require_authentication(self) -> None:
        self.assertEqual(self.client.get("/health/live").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/tasks").status_code, 401)

    def test_disabled_webhooks_return_not_found(self) -> None:
        response = self.client.post("/webhooks/discord", json={"content": "hello"})
        self.assertEqual(response.status_code, 404)
