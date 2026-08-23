"""Gateway: provider construction, response cache, usage ledger, metering.

Deterministic-first/AI-second: the gateway is the ONLY path to a vendor and
it records every call. Cache hits and failures are ledgered too, so usage
is auditable.
"""

import hashlib
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.llm.providers import (
    AnthropicProvider,
    Completion,
    GeminiProvider,
    LLMProviderError,
    OllamaProvider,
    OpenAICompatProvider,
    Provider,
)
from app.persistence.models import LLMRequestRecord, ResponseCacheRecord, utcnow


class LLMUnavailable(RuntimeError):
    """No usable provider configured (or misconfigured) - map to 503."""


class LLMRateLimited(RuntimeError):
    """Daily quota exhausted for this client key - map to 429."""

    def __init__(self, message: str, retry_after_seconds: int) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


_PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "azure": {"base_url": "", "model": ""},
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    "anthropic": {"base_url": "https://api.anthropic.com/v1", "model": "claude-3-5-haiku-latest"},
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.0-flash",
    },
    "ollama": {"base_url": "http://localhost:11434", "model": "llama3.1"},
}


def build_provider() -> Provider | None:
    """Construct the configured provider; ``none`` disables AI features."""
    settings = get_settings()
    name = settings.llm_provider.strip().lower()
    if name in ("", "none", "off"):
        return None
    if name not in _PROVIDER_DEFAULTS:
        raise LLMUnavailable(
            f"unknown SDP_LLM_PROVIDER '{name}' "
            f"(expected one of {', '.join(['none', *sorted(_PROVIDER_DEFAULTS)])})"
        )
    defaults = _PROVIDER_DEFAULTS[name]
    base_url = settings.llm_base_url or defaults["base_url"]
    model = settings.llm_model or defaults["model"]
    key = settings.llm_api_key

    if name == "ollama":
        if not base_url:
            raise LLMUnavailable("ollama requires SDP_LLM_BASE_URL")
        return OllamaProvider(base_url=base_url, model=model)
    if name == "anthropic":
        if not key:
            raise LLMUnavailable("anthropic requires SDP_LLM_API_KEY")
        return AnthropicProvider(api_key=key, base_url=base_url, model=model)
    if name == "gemini":
        if not key:
            raise LLMUnavailable("gemini requires SDP_LLM_API_KEY")
        return GeminiProvider(api_key=key, base_url=base_url, model=model)

    # openai / azure / groq share the OpenAI wire format
    if name == "azure":
        if not base_url or not model:
            raise LLMUnavailable(
                "azure requires SDP_LLM_BASE_URL (deployment root) and SDP_LLM_MODEL"
            )
    elif not key:
        raise LLMUnavailable(f"{name} requires SDP_LLM_API_KEY")
    if not base_url or not model:
        raise LLMUnavailable(f"{name} requires an endpoint/model")
    return OpenAICompatProvider(
        name=name, base_url=base_url, api_key=key, model=model, azure=(name == "azure")
    )


def cache_key(provider_name: str, model: str, prompt_version: str, system: str, user: str) -> str:
    identity = "\x1f".join([provider_name, model, prompt_version, system, user])
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _as_int(value: object) -> int:
    """JSON columns hand back ``object``; coerce defensively."""
    return int(value) if isinstance(value, (int, float)) else 0


@dataclass
class Gateway:
    provider: Provider | None
    daily_limit: int = 200

    def complete(
        self,
        db: Session,
        *,
        task: str,
        owner_key: str | None,
        system: str,
        user: str,
        prompt_version: str = "",
        max_tokens: int = 700,
    ) -> tuple[Completion, bool]:
        """Returns (completion, cache_hit). Ledgered; raises rate/unavailable."""
        if self.provider is None:
            raise LLMUnavailable("no LLM provider configured")

        # Cache lookup comes BEFORE metering: served-from-cache answers stay
        # available even when the daily quota is exhausted.
        key = cache_key(self.provider.name, self._model(), prompt_version, system, user)
        cached = db.get(ResponseCacheRecord, key)
        if cached is not None:
            payload = cached.payload
            completion = Completion(
                text=str(payload.get("text", "")),
                tokens_in=_as_int(payload.get("tokens_in")),
                tokens_out=_as_int(payload.get("tokens_out")),
            )
            db.add(
                LLMRequestRecord(
                    owner_key=owner_key,
                    task=task,
                    provider=self.provider.name,
                    model=self._model(),
                    prompt_version=prompt_version,
                    cache_hit=True,
                )
            )
            return completion, True

        start_of_day = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        used_today = (
            db.query(LLMRequestRecord)
            .filter(
                LLMRequestRecord.owner_key == owner_key,
                LLMRequestRecord.cache_hit.is_(False),
                LLMRequestRecord.error.is_(None),
                LLMRequestRecord.created_at >= start_of_day,
            )
            .count()
        )
        if used_today >= self.daily_limit:
            raise LLMRateLimited(
                f"daily limit of {self.daily_limit} LLM calls reached; resets at UTC midnight",
                retry_after_seconds=3600,
            )

        started = time.perf_counter()
        error: str | None = None
        fresh: Completion | None = None
        try:
            fresh = self.provider.complete(system, user, max_tokens=max_tokens)
        except LLMProviderError as exc:
            error = str(exc)[:500]
        latency_ms = int((time.perf_counter() - started) * 1000)

        db.add(
            LLMRequestRecord(
                owner_key=owner_key,
                task=task,
                provider=self.provider.name,
                model=self._model(),
                prompt_version=prompt_version,
                tokens_in=fresh.tokens_in if fresh else 0,
                tokens_out=fresh.tokens_out if fresh else 0,
                latency_ms=latency_ms,
                cache_hit=False,
                error=error,
            )
        )
        if fresh is None:
            raise LLMProviderError(error or "provider failed")
        completion = fresh
        db.merge(
            ResponseCacheRecord(
                key=key,
                task=task,
                payload=self._payload(completion),
            )
        )
        return completion, False

    def _model(self) -> str:
        p: Any = self.provider
        return getattr(p, "model", "")

    @staticmethod
    def _payload(c: Completion) -> dict[str, Any]:
        return {"text": c.text, "tokens_in": c.tokens_in, "tokens_out": c.tokens_out}


_gateway: Gateway | None = None


def get_gateway() -> Gateway:
    global _gateway
    if _gateway is None:
        try:
            provider = build_provider()
        except LLMUnavailable:
            # A misconfigured provider must not crash the app; AI endpoints
            # degrade loudly (503 / deterministic fallback) instead.
            provider = None
        settings = get_settings()
        _gateway = Gateway(provider=provider, daily_limit=settings.llm_daily_limit)
    return _gateway


def reset_gateway_for_tests() -> None:
    global _gateway
    _gateway = None
