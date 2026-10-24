"""Typed HTTP adapters for common LLM provider APIs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from src.core.settings import AppSettings


class ProviderName(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    GENERIC_OPENAI_COMPATIBLE = "generic_openai_compatible"


class ProviderConfigurationError(ValueError):
    """Raised when a provider lacks required configuration."""


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in {"system", "user", "assistant"}:
            raise ValueError(f"Unsupported message role: {self.role}")
        if not self.content.strip():
            raise ValueError("Message content must not be empty")


@dataclass(frozen=True)
class LLMResponse:
    provider: ProviderName
    model: str
    content: str
    raw: Mapping[str, object]


Transport = Callable[[Request], bytes]


def _default_transport(request: Request) -> bytes:
    try:
        with urlopen(request, timeout=120) as response:
            return response.read()
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"LLM provider request failed: {exc}") from exc


class LLMProvider(Protocol):
    name: ProviderName
    model: str

    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse: ...


class OpenAICompatibleProvider:
    """Adapter for OpenAI, OpenRouter, and compatible chat-completions APIs."""

    def __init__(
        self,
        name: ProviderName,
        api_key: str,
        endpoint: str,
        model: str,
        *,
        transport: Transport = _default_transport,
    ) -> None:
        if not api_key.strip():
            raise ProviderConfigurationError(f"{name.value} API key is required")
        if not endpoint.strip():
            raise ProviderConfigurationError(f"{name.value} endpoint is required")
        if not model.strip():
            raise ProviderConfigurationError(f"{name.value} model is required")
        self.name = name
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self._transport = transport

    def build_request(self, messages: list[LLMMessage], temperature: float) -> Request:
        if not messages:
            raise ValueError("At least one message is required")
        payload = {
            "model": self.model,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if self.name == ProviderName.OPENROUTER:
            headers["HTTP-Referer"] = "https://github.com/Gladiatorsarius/HAPA"
            headers["X-Title"] = "HAPA"
        return Request(
            f"{self.endpoint}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        raw = json.loads(self._transport(self.build_request(messages, temperature)))
        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"{self.name.value} returned an invalid response") from exc
        if not isinstance(content, str):
            raise RuntimeError(f"{self.name.value} returned non-text content")
        return LLMResponse(self.name, self.model, content, raw)


class AnthropicProvider:
    """Adapter for Anthropic's messages API."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        model: str,
        *,
        transport: Transport = _default_transport,
    ) -> None:
        if not api_key.strip():
            raise ProviderConfigurationError("anthropic API key is required")
        self.name = ProviderName.ANTHROPIC
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self._transport = transport

    def build_request(self, messages: list[LLMMessage], temperature: float) -> Request:
        if not messages:
            raise ValueError("At least one message is required")
        system = [message.content for message in messages if message.role == "system"]
        conversation = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role != "system"
        ]
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": conversation,
            "temperature": temperature,
        }
        if system:
            payload["system"] = "\n\n".join(system)
        return Request(
            f"{self.endpoint}/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )

    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        raw = json.loads(self._transport(self.build_request(messages, temperature)))
        try:
            content = raw["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("anthropic returned an invalid response") from exc
        if not isinstance(content, str):
            raise RuntimeError("anthropic returned non-text content")
        return LLMResponse(self.name, self.model, content, raw)


class GeminiProvider:
    """Adapter for Google's Gemini generateContent API."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        model: str,
        *,
        transport: Transport = _default_transport,
    ) -> None:
        if not api_key.strip():
            raise ProviderConfigurationError("google API key is required")
        self.name = ProviderName.GOOGLE
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self._transport = transport

    def build_request(self, messages: list[LLMMessage], temperature: float) -> Request:
        if not messages:
            raise ValueError("At least one message is required")
        payload = {
            "contents": [
                {
                    "role": "model" if message.role == "assistant" else "user",
                    "parts": [{"text": message.content}],
                }
                for message in messages
                if message.role != "system"
            ],
            "generationConfig": {"temperature": temperature},
        }
        return Request(
            f"{self.endpoint}/v1beta/models/{self.model}:generateContent?key={self.api_key}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        raw = json.loads(self._transport(self.build_request(messages, temperature)))
        try:
            content = raw["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("google returned an invalid response") from exc
        if not isinstance(content, str):
            raise RuntimeError("google returned non-text content")
        return LLMResponse(self.name, self.model, content, raw)


def create_provider(
    name: ProviderName | str,
    *,
    transport: Transport = _default_transport,
    environ: Mapping[str, str] | None = None,
) -> LLMProvider:
    """Create a configured provider from environment variables."""

    load_dotenv()
    provider_name = ProviderName(name)
    env = os.environ if environ is None else environ
    prefix = provider_name.value.upper()
    api_key = env.get(f"{prefix}_API_KEY", "")
    endpoint_defaults = {
        ProviderName.OPENAI: "https://api.openai.com/v1",
        ProviderName.ANTHROPIC: "https://api.anthropic.com",
        ProviderName.GOOGLE: "https://generativelanguage.googleapis.com",
        ProviderName.OPENROUTER: "https://openrouter.ai/api/v1",
        ProviderName.GENERIC_OPENAI_COMPATIBLE: "",
    }
    endpoint = env.get(f"{prefix}_BASE_URL", endpoint_defaults[provider_name])
    model = env.get(f"{prefix}_MODEL", "")
    if not model:
        raise ProviderConfigurationError(f"{provider_name.value} model is required")
    if provider_name == ProviderName.ANTHROPIC:
        return AnthropicProvider(api_key, endpoint, model, transport=transport)
    if provider_name == ProviderName.GOOGLE:
        return GeminiProvider(api_key, endpoint, model, transport=transport)
    return OpenAICompatibleProvider(
        provider_name,
        api_key,
        endpoint,
        model,
        transport=transport,
    )


def create_configured_provider(
    settings: AppSettings,
    *,
    transport: Transport = _default_transport,
    environ: Mapping[str, str] | None = None,
) -> LLMProvider:
    """Create the single active provider using the YAML-selected strong model."""

    load_dotenv()
    env = os.environ if environ is None else environ
    provider_name = ProviderName(settings.llm.active_provider)
    prefix = provider_name.value.upper()
    api_key = env.get(f"{prefix}_API_KEY", "")
    endpoint_defaults = {
        ProviderName.OPENAI: "https://api.openai.com/v1",
        ProviderName.ANTHROPIC: "https://api.anthropic.com",
        ProviderName.GOOGLE: "https://generativelanguage.googleapis.com",
        ProviderName.OPENROUTER: "https://openrouter.ai/api/v1",
        ProviderName.GENERIC_OPENAI_COMPATIBLE: "",
    }
    endpoint = env.get(f"{prefix}_BASE_URL", endpoint_defaults[provider_name])
    if provider_name == ProviderName.ANTHROPIC:
        return AnthropicProvider(
            api_key, endpoint, settings.llm.strong_model, transport=transport
        )
    if provider_name == ProviderName.GOOGLE:
        return GeminiProvider(
            api_key, endpoint, settings.llm.strong_model, transport=transport
        )
    return OpenAICompatibleProvider(
        provider_name,
        api_key,
        endpoint,
        settings.llm.strong_model,
        transport=transport,
    )


__all__ = [
    "AnthropicProvider",
    "GeminiProvider",
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "OpenAICompatibleProvider",
    "ProviderConfigurationError",
    "ProviderName",
    "create_configured_provider",
    "create_provider",
]
