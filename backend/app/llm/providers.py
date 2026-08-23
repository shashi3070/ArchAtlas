"""Provider protocol and REST adapters (OpenAI-compatible, Anthropic,
Gemini, Ollama). No vendor SDKs - httpx only.
"""

from dataclasses import dataclass
from typing import Any, Protocol

import httpx


@dataclass
class Completion:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0


class LLMProviderError(RuntimeError):
    """Raised when the upstream call fails or returns an unusable body."""


class Provider(Protocol):
    name: str

    def complete(self, system: str, user: str, *, max_tokens: int) -> Completion: ...


_TIMEOUT = httpx.Timeout(60.0)


def _post(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=_TIMEOUT)
    except httpx.HTTPError as exc:
        raise LLMProviderError(f"transport error: {exc}") from exc
    if resp.status_code >= 400:
        raise LLMProviderError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    try:
        payload: dict[str, Any] = resp.json()
    except ValueError as exc:
        raise LLMProviderError("response was not JSON") from exc
    return payload


@dataclass
class OpenAICompatProvider:
    """Chat completions for OpenAI, Azure OpenAI (v1 endpoint) and Groq."""

    name: str
    base_url: str
    api_key: str
    model: str
    azure: bool = False

    def complete(self, system: str, user: str, *, max_tokens: int) -> Completion:
        headers = {"Content-Type": "application/json"}
        if self.azure:
            headers["api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = _post(
            f"{self.base_url.rstrip('/')}/chat/completions",
            headers,
            {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(f"unexpected response shape: {str(data)[:200]}") from exc
        usage = data.get("usage") or {}
        return Completion(
            text=text or "",
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
        )


@dataclass
class AnthropicProvider:
    name: str = "anthropic"
    api_key: str = ""
    base_url: str = "https://api.anthropic.com/v1"
    model: str = "claude-3-5-haiku-latest"

    def complete(self, system: str, user: str, *, max_tokens: int) -> Completion:
        data = _post(
            f"{self.base_url.rstrip('/')}/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            body={
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        usage = data.get("usage") or {}
        return Completion(
            text=text,
            tokens_in=int(usage.get("input_tokens") or 0),
            tokens_out=int(usage.get("output_tokens") or 0),
        )


@dataclass
class GeminiProvider:
    name: str = "gemini"
    api_key: str = ""
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    model: str = "gemini-2.0-flash"

    def complete(self, system: str, user: str, *, max_tokens: int) -> Completion:
        data = _post(
            f"{self.base_url.rstrip('/')}/models/{self.model}:generateContent?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            body={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
        )
        candidates = data.get("candidates") or []
        parts = (
            candidates[0].get("content", {}).get("parts", []) if candidates else []
        )
        text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata") or {}
        return Completion(
            text=text,
            tokens_in=int(usage.get("promptTokenCount") or 0),
            tokens_out=int(usage.get("candidatesTokenCount") or 0),
        )


@dataclass
class OllamaProvider:
    """Local Ollama (/api/chat). No API key required."""

    name: str = "ollama"
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1"

    def complete(self, system: str, user: str, *, max_tokens: int) -> Completion:
        data = _post(
            f"{self.base_url.rstrip('/')}/api/chat",
            headers={"Content-Type": "application/json"},
            body={
                "model": self.model,
                "stream": False,
                "options": {"num_predict": max_tokens},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        message = data.get("message") or {}
        return Completion(
            text=message.get("content") or "",
            tokens_in=int(data.get("prompt_eval_count") or 0),
            tokens_out=int(data.get("eval_count") or 0),
        )
