import base64
import hashlib
import hmac
import json
import tempfile
import time
from pathlib import Path
from unittest import TestCase
from src.api.auth import decode_jwt
from src.api.store import ApiStore
from src.core.settings import AuthSettings
from src.tiers.tier1_supervisor.state import create_initial_state


class FoundationTests(TestCase):
    def test_store_persists_tasks_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ApiStore(f"sqlite:///{directory}/hapa.db")
            state = create_initial_state(title="Test", description="", requested_by="test")
            task_id = state["metadata"].task_id
            task = store.create_task(
                {
                    "task_id": task_id,
                    "title": "Test",
                    "description": "",
                    "lineage": state["lineage"].model_dump(mode="json"),
                    "provenance": state["metadata"].provenance.model_dump(mode="json"),
                },
                "PENDING",
                False,
            )
            store.add_event(task_id, "created", {"state": "PENDING"})
            self.assertEqual(store.get_task(task_id)["title"], "Test")
            self.assertEqual(store.get_task(task_id)["provenance"]["source"], "api")
            self.assertEqual(store.list_events(task_id)[0]["event_type"], "created")
            store.close()

    def test_decode_jwt_validates_signature_and_claims(self) -> None:
        settings = AuthSettings(issuer_url="issuer", audience="aud", jwt_secret="secret")
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"iss": "issuer", "aud": "aud", "exp": time.time() + 60, "scope": "hapa:read"}
        enc = lambda value: base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=").decode()
        signing_input = f"{enc(header)}.{enc(payload)}"
        signature = base64.urlsafe_b64encode(hmac.new(b"secret", signing_input.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
        self.assertEqual(decode_jwt(f"{signing_input}.{signature}", settings)["scope"], "hapa:read")

    def test_approval_decision_requires_valid_state_and_preserves_comment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ApiStore(f"sqlite:///{directory}/hapa.db")
            task_id = create_initial_state(
                title="Deploy",
                description="Deploy",
                requested_by="test",
            )["metadata"].task_id
            approval_id = task_id
            store.add_approval(task_id, approval_id)

            with self.assertRaises(ValueError):
                store.decide_approval(approval_id, "RUNNING")

            approval = store.decide_approval(approval_id, "REJECTED", "Not ready")
            self.assertEqual(approval["comment"], "Not ready")
            self.assertEqual(approval["state"], "REJECTED")
            store.close()
