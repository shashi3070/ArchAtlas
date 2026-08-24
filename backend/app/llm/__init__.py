"""LLM gateway: multi-provider access behind one protocol (Phase 5).

Providers are thin REST adapters - no vendor SDKs - so domain code never
imports a vendor library. One OpenAI-compatible adapter covers OpenAI,
Azure OpenAI (v1 endpoint) and Groq; Anthropic, Gemini and Ollama have
their own adapters.
"""

from app.llm.gateway import (
    Gateway,
    LLMRateLimited,
    LLMUnavailable,
    build_named_provider,
    get_gateway,
    list_providers,
    reset_gateway_for_tests,
)
from app.llm.providers import Completion, LLMProviderError, Provider

__all__ = [
    "Completion",
    "Gateway",
    "LLMProviderError",
    "LLMRateLimited",
    "LLMUnavailable",
    "Provider",
    "build_named_provider",
    "get_gateway",
    "list_providers",
    "reset_gateway_for_tests",
]
