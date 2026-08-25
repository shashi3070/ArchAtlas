"""JWT creation and verification for ArchAtlas sessions.

Issues short-lived access tokens after Google OAuth verification.
Tokens carry: sub, email, name, picture, tier, exp, iat.
"""

import time
from typing import Any

import jwt as pyjwt

_DEFAULT_SECRET = "change-me-in-production"
_DEFAULT_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours


def create_access_token(
    payload: dict[str, Any],
    secret: str = "",
    expires_in: int = _ACCESS_TOKEN_EXPIRES,
) -> str:
    """Create a signed JWT access token."""
    secret = secret or _DEFAULT_SECRET
    now = int(time.time())
    claims = {
        **payload,
        "iat": now,
        "exp": now + expires_in,
    }
    return pyjwt.encode(claims, secret, algorithm=_DEFAULT_ALGORITHM)


def decode_access_token(token: str, secret: str = "") -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Returns the decoded payload dict.
    Raises JWTError on any verification failure.
    """
    secret = secret or _DEFAULT_SECRET
    return pyjwt.decode(token, secret, algorithms=[_DEFAULT_ALGORITHM])
