import json
from unittest import TestCase
from urllib.request import Request

from src.llm.providers import (
    GeminiProvider,
    LLMMessage,
    OpenAICompatibleProvider,
    ProviderConfigurationError,
    ProviderName,
    create_provider,
)


def transport_for(payload: dict[str, object]):
    def transport(request: Request) -> bytes:
        transport.request = request
        return json.dumps(payload).encode("utf-8")

    return transport


class ProviderTests(TestCase):
    def test_anthropic_provider_builds_messages_request(self) -> None:
        provider = create_provider(
            "anthropic",
            environ={"ANTHROPIC_API_KEY": "secret", "ANTHROPIC_MODEL": "claude"},
            transport=transport_for({"content": [{"text": "hello"}]}),
        )

        response = provider.complete(
            [LLMMessage("system", "Be concise"), LLMMessage("user", "Hi")]
        )

        self.assertEqual(response.content, "hello")
        self.assertEqual(response.provider, ProviderName.ANTHROPIC)

    def test_openai_compatible_provider_builds_chat_request(self) -> None:
        provider = create_provider(
            "openai",
            environ={"OPENAI_API_KEY": "secret", "OPENAI_MODEL": "gpt-test"},
            transport=transport_for(
                {"choices": [{"message": {"content": "hello"}}]}
            ),
        )

        response = provider.complete([LLMMessage("user", "Hi")])

        self.assertEqual(response.content, "hello")
        self.assertEqual(response.provider, ProviderName.OPENAI)

    def test_generic_compatible_endpoint_is_supported(self) -> None:
        provider = create_provider(
            ProviderName.GENERIC_OPENAI_COMPATIBLE,
            environ={
                "GENERIC_OPENAI_COMPATIBLE_API_KEY": "secret",
                "GENERIC_OPENAI_COMPATIBLE_BASE_URL": "https://llm.test/v1",
                "GENERIC_OPENAI_COMPATIBLE_MODEL": "local",
            },
            transport=transport_for(
                {"choices": [{"message": {"content": "hello"}}]}
            ),
        )

        self.assertIsInstance(provider, OpenAICompatibleProvider)
        self.assertEqual(provider.endpoint, "https://llm.test/v1")

    def test_google_provider_returns_text(self) -> None:
        provider = GeminiProvider(
            "secret",
            "https://generativelanguage.googleapis.com",
            "gemini",
            transport=transport_for(
                {"candidates": [{"content": {"parts": [{"text": "hello"}]}}]}
            ),
        )

        self.assertEqual(provider.complete([LLMMessage("user", "Hi")]).content, "hello")

    def test_missing_model_is_explicit(self) -> None:
        with self.assertRaises(ProviderConfigurationError):
            create_provider("openai", environ={"OPENAI_API_KEY": "secret"})
