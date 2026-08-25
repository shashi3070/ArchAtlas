"""FastAPI dependencies for authentication and rate limiting."""

import time
from collections import defaultdict
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_access_token
from app.core.config import get_settings

_bearer = HTTPBearer(auto_error=False)


async def _extract_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> HTTPAuthorizationCredentials | None:
    return credentials


def _decode_token(credentials: HTTPAuthorizationCredentials | None) -> dict[str, Any]:
    """Decode and return token payload, or empty dict on failure."""
    if credentials is None:
        return {}
    settings = get_settings()
    try:
        return decode_access_token(credentials.credentials, settings.jwt_secret)
    except Exception:
        return {}


def _get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_extract_credentials),
) -> dict[str, Any]:
    """Extract and verify the current user from the Authorization header.

    Returns a dict with: sub, email, name, picture, tier.
    Raises 401 if no valid token.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_token(credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_extract_credentials),
) -> dict[str, Any]:
    """Public dependency: returns user dict or None for unauthenticated access."""
    return _decode_token(credentials)


# ── Rate limiting ──────────────────────────────────────────────

# In-memory rate limit stores (production would use Redis)
_daily_counts: dict[str, int] = defaultdict(int)  # owner_key -> count today
_last_request: dict[str, float] = {}  # owner_key -> timestamp of last request
_daily_reset_date: dict[str, str] = {}  # owner_key -> YYYY-MM-DD


def _today_key() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).strftime("%Y-%m-%d")


def _get_owner_key(user: dict[str, Any]) -> str:
    """Extract owner key from user dict (email or sub)."""
    return user.get("email") or user.get("sub") or ""


def _check_daily_limit(owner_key: str, limit: int) -> None:
    """Raise 429 if daily limit exceeded."""
    today = _today_key()
    if _daily_reset_date.get(owner_key) != today:
        _daily_counts[owner_key] = 0
        _daily_reset_date[owner_key] = today
    if _daily_counts[owner_key] >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit of {limit} requests reached. Resets at midnight UTC.",
            headers={"Retry-After": "3600"},
        )


def _check_cooldown(owner_key: str, min_seconds: float) -> None:
    """Raise 429 if request comes too soon after the last one."""
    now = time.monotonic()
    last = _last_request.get(owner_key, 0.0)
    wait = min_seconds - (now - last)
    if wait > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit: wait {wait:.1f}s before next request",
            headers={"Retry-After": str(int(wait) + 1)},
        )
    _last_request[owner_key] = now


def _record_request(owner_key: str) -> None:
    """Record a completed request."""
    today = _today_key()
    if _daily_reset_date.get(owner_key) != today:
        _daily_counts[owner_key] = 0
        _daily_reset_date[owner_key] = today
    _daily_counts[owner_key] += 1


def check_rate_limit(
    user: dict[str, Any], *, is_free_groq_model: bool = False
) -> None:
    """Enforce rate limits based on user tier.

    Free users: 100 agentic API requests/day, 10s cooldown per request.
    Free Groq models: 1000 requests/day per user, 10s cooldown.
    Premium users: no limits.
    """
    tier = user.get("tier", "free")
    if tier == "premium":
        return  # no limits for premium

    owner_key = _get_owner_key(user)
    if not owner_key:
        return  # anonymous - skip rate limiting

    daily_limit = 1000 if is_free_groq_model else 100
    _check_daily_limit(owner_key, daily_limit)
    _check_cooldown(owner_key, 10.0)


def get_rate_limit_status(user: dict[str, Any]) -> dict[str, Any]:
    """Return current rate limit status for the user."""
    owner_key = _get_owner_key(user)
    today = _today_key()
    if _daily_reset_date.get(owner_key) != today:
        used = 0
    else:
        used = _daily_counts.get(owner_key, 0)

    tier = user.get("tier", "free")
    daily_limit = 1000 if tier == "free" else -1  # -1 = unlimited
    last_ts = _last_request.get(owner_key, 0.0)
    cooldown_remaining = max(0, 10.0 - (time.monotonic() - last_ts))

    return {
        "tier": tier,
        "daily_limit": daily_limit,
        "used_today": used,
        "remaining": max(0, daily_limit - used) if daily_limit > 0 else -1,
        "cooldown_seconds": round(cooldown_remaining, 1),
    }
