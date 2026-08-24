"""Gateway: provider construction, response cache, usage ledger, metering.

Deterministic-first/AI-second: the gateway is the ONLY path to a vendor and
it records every call. Cache hits and failures are ledgered too, so usage
is auditable.
"""

import hashlib
import time
from dataclasses import dataclass, replace
from typing import Any

import httpx
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
        "model": "openai/gpt-oss-120b",
    },
    "anthropic": {"base_url": "https://api.anthropic.com/v1", "model": "claude-3-5-haiku-latest"},
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.0-flash",
    },
    "ollama": {"base_url": "http://localhost:11434", "model": "llama3.1"},
}

_PROVIDER_LABELS = {
    "openai": "OpenAI",
    "azure": "Azure OpenAI",
    "groq": "Groq",
    "anthropic": "Anthropic Claude",
    "gemini": "Gemini",
    "ollama": "Ollama (local)",
}

_DEDICATED_KEY_FIELDS = {
    "openai": "openai_api_key",
    "azure": "azure_api_key",
    "groq": "groq_api_key",
    "anthropic": "anthropic_api_key",
    "gemini": "gemini_api_key",
}


def _key_for(name: str, settings: Any) -> str:
    """Dedicated per-provider key wins; SDP_LLM_API_KEY applies to the
    provider named as the active default only."""
    field = _DEDICATED_KEY_FIELDS.get(name)
    dedicated = str(getattr(settings, field, "") or "") if field else ""
    if dedicated:
        return dedicated
    if name == settings.llm_provider:
        return settings.llm_api_key or ""
    return ""


def build_named_provider(name: str, settings: Any | None = None) -> Provider | None:
    """Construct a provider by id; ``none``/empty returns None. Raises
    LLMUnavailable with a precise, user-facing reason when unusable."""
    settings = settings or get_settings()
    name = name.strip().lower()
    if name in ("", "none", "off"):
        return None
    if name not in _PROVIDER_DEFAULTS:
        raise LLMUnavailable(
            f"unknown provider '{name}' "
            f"(expected one of {', '.join(['none', *sorted(_PROVIDER_DEFAULTS)])})"
        )
    defaults = _PROVIDER_DEFAULTS[name]
    base_url = (settings.llm_base_url if name == settings.llm_provider else "") or (
        defaults["base_url"]
    )
    model = (settings.llm_model if name == settings.llm_provider else "") or defaults["model"]
    key = _key_for(name, settings)

    if name == "ollama":
        return OllamaProvider(base_url=base_url, model=model)
    if not key:
        raise LLMUnavailable(f"no API key available for {_PROVIDER_LABELS[name]}")
    if name == "anthropic":
        return AnthropicProvider(api_key=key, base_url=base_url, model=model)
    if name == "gemini":
        return GeminiProvider(api_key=key, base_url=base_url, model=model)
    # openai / azure / groq share the OpenAI wire format
    if not base_url or not model:
        raise LLMUnavailable(
            f"{_PROVIDER_LABELS[name]} requires an endpoint and model"
            + (" (set SDP_LLM_BASE_URL and SDP_LLM_MODEL)" if name == "azure" else "")
        )
    return OpenAICompatProvider(
        name=name, base_url=base_url, api_key=key, model=model, azure=(name == "azure")
    )


def build_provider() -> Provider | None:
    """Construct the configured default provider; ``none`` disables AI."""
    return build_named_provider(get_settings().llm_provider)


def list_providers() -> list[dict[str, Any]]:
    """UI-facing availability matrix. Never exposes key values."""
    settings = get_settings()
    out: list[dict[str, Any]] = []
    for pid in sorted(_PROVIDER_DEFAULTS):
        requires_key = pid != "ollama"
        out.append(
            {
                "id": pid,
                "label": _PROVIDER_LABELS[pid],
                "requires_key": requires_key,
                "key_present": (not requires_key) or bool(_key_for(pid, settings)),
                "default_model": defaults_model(pid, settings),
                "active": pid == settings.llm_provider,
            }
        )
    return out


def defaults_model(pid: str, settings: Any) -> str:
    override = settings.llm_model if pid == settings.llm_provider else ""
    return override or _PROVIDER_DEFAULTS[pid]["model"]


# Model ids that are not chat-completion models (speech, guards, embeddings).
_NON_CHAT_MARKERS = (
    "whisper",
    "orpheus",
    "prompt-guard",
    "safeguard",
    "embed",
    "tts",
    "rerank",
    "guard",
)

_MODEL_CACHE: dict[str, tuple[float, list[str]]] = {}
_MODEL_CACHE_TTL = 600.0  # seconds

_models_http_get: Any = httpx.get  # patchable in tests


def _is_chat_model(model_id: str) -> bool:
    lowered = model_id.lower()
    return not any(marker in lowered for marker in _NON_CHAT_MARKERS)


def list_provider_models(pid: str) -> list[str]:
    """Chat-capable model ids for a provider, fetched live from its /models
    endpoint. Raises LLMUnavailable when the provider is unusable; transport
    failures raise LLMProviderError. Results are cached for 10 minutes."""
    provider = build_named_provider(pid)
    if provider is None:
        return []
    now = time.monotonic()
    cached = _MODEL_CACHE.get(pid)
    if cached is not None and now - cached[0] < _MODEL_CACHE_TTL:
        return list(cached[1])

    ids: list[str] = []
    headers: dict[str, str] = {"Content-Type": "application/json"}
    url = ""
    if isinstance(provider, OpenAICompatProvider):
        url = f"{provider.base_url.rstrip('/')}/models"
        if provider.azure:
            headers["api-key"] = provider.api_key
        else:
            headers["Authorization"] = f"Bearer {provider.api_key}"
    elif isinstance(provider, AnthropicProvider):
        url = f"{provider.base_url.rstrip('/')}/models"
        headers["x-api-key"] = provider.api_key
        headers["anthropic-version"] = "2023-06-01"
    elif isinstance(provider, GeminiProvider):
        url = f"{provider.base_url.rstrip('/')}/models?key={provider.api_key}"
    elif isinstance(provider, OllamaProvider):
        url = f"{provider.base_url.rstrip('/')}/api/tags"
    else:  # pragma: no cover - future provider kinds
        raise LLMProviderError(f"model listing unsupported for {provider.name}")

    try:
        resp = _models_http_get(url, headers=headers, timeout=20.0)
    except httpx.HTTPError as exc:
        raise LLMProviderError(f"transport error listing models: {exc}") from exc
    if resp.status_code >= 400:
        raise LLMProviderError(f"HTTP {resp.status_code} listing models")
    try:
        payload: dict[str, Any] = resp.json()
    except ValueError as exc:
        raise LLMProviderError("model list was not JSON") from exc

    raw = payload.get("data") or payload.get("models") or []
    for entry in raw:
        mid = entry.get("id") or entry.get("name") or ""
        if mid.startswith("models/"):
            mid = mid[len("models/") :]
        if mid and _is_chat_model(mid):
            ids.append(mid)

    result = sorted(set(ids))
    _MODEL_CACHE[pid] = (now, result)
    return result


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

    def __post_init__(self) -> None:
        self._overrides: dict[str, Provider] = {}

    def provider_by_name(self, name: str) -> Provider | None:
        """Resolve a named provider (lazily built + cached); empty means the
        configured default. Raises LLMUnavailable with a precise reason."""
        if not name or name.strip().lower() in ("", "default"):
            return self.provider
        pid = name.strip().lower()
        if pid in self._overrides:
            return self._overrides[pid]
        resolved = build_named_provider(pid)
        self._overrides[pid] = resolved  # type: ignore[assignment]
        return resolved

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
        provider_id: str = "",
        model_override: str = "",
        json_mode: bool = False,
    ) -> tuple[Completion, bool]:
        """Returns (completion, cache_hit). Ledgered; raises rate/unavailable.
        ``model_override`` swaps the model on a per-call basis (UI picker);
        cache identity includes the effective model either way."""
        active = self.provider_by_name(provider_id)
        if active is None:
            raise LLMUnavailable(
                f"no API key available for '{provider_id}'"
                if provider_id
                else "no LLM provider configured"
            )
        if model_override and model_override != getattr(active, "model", ""):
            try:
                active = replace(active, model=model_override)  # type: ignore[type-var]
            except TypeError as exc:
                raise LLMUnavailable(
                    f"provider '{active.name}' does not support model overrides"
                ) from exc
        active_model = getattr(active, "model", "")

        # Cache lookup comes BEFORE metering: served-from-cache answers stay
        # available even when the daily quota is exhausted.
        key = cache_key(active.name, active_model, prompt_version, system, user)
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
                    provider=active.name,
                    model=active_model,
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
            fresh = active.complete(system, user, max_tokens=max_tokens, json_mode=json_mode)
        except LLMProviderError as exc:
            error = str(exc)[:500]
        latency_ms = int((time.perf_counter() - started) * 1000)

        db.add(
            LLMRequestRecord(
                owner_key=owner_key,
                task=task,
                provider=active.name,
                model=active_model,
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
