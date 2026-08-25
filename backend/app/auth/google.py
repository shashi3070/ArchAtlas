"""Google OAuth token verification (no SDK - httpx only).

Verifies Google ID tokens by fetching Google's public JWKS and validating
the JWT signature, expiry, issuer, and audience.
"""

import time
from typing import Any

import httpx
from jose import jwt

_GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/tokeninfo"
_GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}

_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 3600.0  # 1 hour


def _fetch_jwks() -> dict[str, Any]:
    """Fetch Google's public signing keys (cached for 1 hour)."""
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if _jwks_cache and now - _jwks_fetched_at < _JWKS_TTL:
        return _jwks_cache
    resp = httpx.get(_GOOGLE_JWKS_URL, timeout=10.0)
    resp.raise_for_status()
    _jwks_cache = resp.json()
    _jwks_fetched_at = now
    return _jwks_cache


def verify_google_token(id_token: str, client_id: str) -> dict[str, Any]:
    """Verify a Google ID token and return the decoded payload.

    Returns a dict with at minimum: sub, email, name, picture.
    Raises ValueError on any verification failure.
    """
    if not client_id:
        raise ValueError("Google OAuth client ID not configured")

    # Strategy 1: Verify locally using JWKS (preferred - no extra HTTP call)
    try:
        payload = _verify_with_jwks(id_token, client_id)
        return payload
    except Exception:
        pass

    # Strategy 2: Fallback to Google's tokeninfo endpoint
    return _verify_with_tokeninfo(id_token, client_id)


def _verify_with_jwks(id_token: str, client_id: str) -> dict[str, Any]:
    """Verify using Google's public JWKS."""
    jwks = _fetch_jwks()
    header = jwt.get_unverified_header(id_token)
    kid = header.get("kid")

    key_data = None
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            key_data = key
            break

    if key_data is None:
        raise ValueError("No matching key found in Google JWKS")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
    payload: dict[str, Any] = jwt.decode(
        id_token,
        public_key,
        algorithms=["RS256"],
        audience=client_id,
        issuer=_GOOGLE_ISSUERS,
    )

    if "sub" not in payload or "email" not in payload:
        raise ValueError("Token missing required claims (sub, email)")

    return payload


def _verify_with_tokeninfo(id_token: str, client_id: str) -> dict[str, Any]:
    """Fallback: verify via Google's tokeninfo endpoint."""
    resp = httpx.get(
        _GOOGLE_TOKEN_URL,
        params={"id_token": id_token},
        timeout=10.0,
    )
    if resp.status_code != 200:
        raise ValueError(f"Google tokeninfo returned {resp.status_code}")

    payload = resp.json()
    if payload.get("aud") != client_id:
        raise ValueError("Token audience mismatch")
    if payload.get("email_verified") != "true":
        raise ValueError("Email not verified by Google")
    if "sub" not in payload or "email" not in payload:
        raise ValueError("Token missing required claims")

    return payload
