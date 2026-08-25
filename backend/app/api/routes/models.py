"""Groq models endpoint with rate limits and capabilities.

Lists all available Groq chat-completion models with their rate limits
from the user's table.
"""

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/models", tags=["models"])

# Groq free-tier model limits (as of 2026)
GROQ_MODELS: list[dict[str, Any]] = [
    {
        "id": "allam-2-7b",
        "label": "Allam 2 7B",
        "requests_per_minute": 30,
        "requests_per_day": 7000,
        "tokens_per_minute": 6000,
        "tokens_per_day": 500000,
        "free": True,
    },
    {
        "id": "groq/compound",
        "label": "Groq Compound",
        "requests_per_minute": 30,
        "requests_per_day": 250,
        "tokens_per_minute": 70000,
        "tokens_per_day": -1,  # no limit
        "free": True,
    },
    {
        "id": "groq/compound-mini",
        "label": "Groq Compound Mini",
        "requests_per_minute": 30,
        "requests_per_day": 250,
        "tokens_per_minute": 70000,
        "tokens_per_day": -1,  # no limit
        "free": True,
    },
    {
        "id": "meta-llama/llama-prompt-guard-2-22m",
        "label": "Llama Prompt Guard 2 22M",
        "requests_per_minute": 30,
        "requests_per_day": 14400,
        "tokens_per_minute": 15000,
        "tokens_per_day": 500000,
        "free": True,
        "note": "Guard model - not for chat completions",
    },
    {
        "id": "meta-llama/llama-prompt-guard-2-86m",
        "label": "Llama Prompt Guard 2 86M",
        "requests_per_minute": 30,
        "requests_per_day": 14400,
        "tokens_per_minute": 15000,
        "tokens_per_day": 500000,
        "free": True,
        "note": "Guard model - not for chat completions",
    },
    {
        "id": "openai/gpt-oss-120b",
        "label": "GPT-OSS 120B",
        "requests_per_minute": 30,
        "requests_per_day": 1000,
        "tokens_per_minute": 8000,
        "tokens_per_day": 200000,
        "free": True,
    },
    {
        "id": "openai/gpt-oss-20b",
        "label": "GPT-OSS 20B",
        "requests_per_minute": 30,
        "requests_per_day": 1000,
        "tokens_per_minute": 8000,
        "tokens_per_day": 200000,
        "free": True,
    },
    {
        "id": "openai/gpt-oss-safeguard-20b",
        "label": "GPT-OSS Safeguard 20B",
        "requests_per_minute": 30,
        "requests_per_day": 1000,
        "tokens_per_minute": 8000,
        "tokens_per_day": 200000,
        "free": True,
        "note": "Guard model - not for chat completions",
    },
    {
        "id": "qwen/qwen3.6-27b",
        "label": "Qwen 3.6 27B",
        "requests_per_minute": 30,
        "requests_per_day": 1000,
        "tokens_per_minute": 8000,
        "tokens_per_day": 200000,
        "free": True,
    },
]

# Free models on ArchAtlas: allow 1000 requests/day per user, 10s cooldown
FREE_MODEL_DAILY_LIMIT = 1000
FREE_MODEL_COOLDOWN_SECONDS = 10


@router.get("/groq")
def list_groq_models() -> dict[str, Any]:
    """List all Groq models with their rate limits."""
    return {
        "provider": "groq",
        "free_tier_limits": {
            "requests_per_day_per_user": FREE_MODEL_DAILY_LIMIT,
            "cooldown_seconds": FREE_MODEL_COOLDOWN_SECONDS,
        },
        "models": GROQ_MODELS,
    }


@router.get("/groq/detail")
def get_groq_model(model_id: str = "") -> dict[str, Any]:
    """Get details for a specific Groq model (pass ?model_id=openai/gpt-oss-120b)."""
    if not model_id:
        return {"error": "model_id query parameter is required"}
    for m in GROQ_MODELS:
        if m["id"] == model_id:
            return m
    return {"error": f"Model '{model_id}' not found"}
