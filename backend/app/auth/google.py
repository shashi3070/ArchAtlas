"""Google OAuth token verification (no SDK - httpx + PyJWT).

Verifies Google ID tokens by fetching Google's public JWKS and validating
the JWT signature, expiry, issuer, and audience.
"""

import time

import httpx
import jwt as pyjwt

_GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_GOOGLE_ISSUER = "https://accounts.google.com"

_jwks_cache: dict[str, list[dict]] = []
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 3600.0  # 1 hour


def _fetch_jwks() -> list[dict]:
    """Fetch Google's public signing keys (cached for 1 hour)."""
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if _jwks_cache and now - _jwks_fetched_at < _JWKS_TTL:
        return _jwks_cache
    resp = httpx.get(_GOOGLE_JWKS_URL, timeout=10.0)
    resp.raise_for_status()
    _jwks_cache = resp.json().get("keys", [])
    _jwks_fetched_at = now
    return _jwks_cache


def verify_google_token(id_token: str, client_id: str) -> dict[str, str]:
    """Verify a Google ID token and return the decoded payload.

    Returns a dict with at minimum: sub, email, name, picture.
    Raises ValueError on any verification failure.
    """
    if not client_id:
        raise ValueError("Google OAuth client ID not configured")

    # Strategy 1: Verify locally using JWKS (preferred)
    try:
        return _verify_with_jwks(id_token, client_id)
    except Exception:
        pass

    # Strategy 2: Fallback to Google's tokeninfo endpoint
    return _verify_with_tokeninfo(id_token, client_id)


def _verify_with_jwks(id_token: str, client_id: str) -> dict[str, str]:
    """Verify using Google's public JWKS via PyJWT."""
    jwks = _fetch_jwks()
    header = pyjwt.get_unverified_header(id_token)
    kid = header.get("kid")

    key_data = None
    for key in jwks:
        if key.get("kid") == kid:
            key_data = key
            break

    if key_data is None:
        raise ValueError("No matching key found in Google JWKS")

    public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(key_data)
    payload: dict[str, str] = pyjwt.decode(
        id_token,
        public_key,
        algorithms=["RS256"],
        audience=client_id,
        issuer=_GOOGLE_ISSUER,
    )

    if "sub" not in payload or "email" not in payload:
        raise ValueError("Token missing required claims (sub, email)")

    return payload


def _verify_with_tokeninfo(id_token: str, client_id: str) -> dict[str, str]:
    """Fallback: verify via Google's tokeninfo endpoint."""
    resp = httpx.get(
        _GOOGLE_TOKENINFO_URL,
        params={"id_token": id_token},
        timeout=10.0,
    )
    if resp.status_code != 200:
        raise ValueError(f"Google tokeninfo returned {resp.status_code}")

    payload = resp.json()
    if payload.get("aud") != client_id:
        raise ValueError("Token audience mismatch")

    # tokeninfo doesn't return email_verified as bool — it's a string
    if payload.get("email_verified") not in ("true", True):
        raise ValueError("Email not verified by Google")

    if "sub" not in payload or "email" not in payload:
        raise ValueError("Token missing required claims")

    return payload
