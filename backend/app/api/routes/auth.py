"""Auth API endpoints: Google OAuth login, token refresh, user profile."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    _get_current_user,
    get_current_user,
    get_rate_limit_status,
)
from app.auth.google import verify_google_token
from app.auth.jwt import create_access_token
from app.auth.models import User
from app.core.config import get_settings
from app.db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[dict[str, Any], Depends(_get_current_user)]
OptionalUser = Annotated[dict[str, Any], Depends(get_current_user)]


class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


def _upsert_user(db: Session, profile: dict[str, Any]) -> User:
    """Find or create user from Google profile. Returns User."""
    user_id = profile.get("sub", "")
    email = profile.get("email", "")
    existing = db.query(User).filter(User.id == user_id).first()
    if existing:
        existing.name = profile.get("name", existing.name)
        existing.picture = profile.get("picture", existing.picture)
        existing.email = email
        db.commit()
        return existing
    user = User(
        id=user_id,
        email=email,
        name=profile.get("name", ""),
        picture=profile.get("picture", ""),
        tier="free",
    )
    db.add(user)
    db.commit()
    return user


@router.post("/google")
def google_login(
    req: GoogleLoginRequest,
    db: DbSession,
) -> AuthResponse:
    """Exchange a Google ID token for an ArchAtlas JWT."""
    settings = get_settings()
    client_id = settings.google_client_id
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured (missing SDP_GOOGLE_CLIENT_ID)",
        )

    try:
        profile = verify_google_token(req.credential, client_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {exc}",
        ) from exc

    user = _upsert_user(db, profile)
    access_token = create_access_token(
        {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "tier": user.tier,
        },
        secret=settings.jwt_secret,
    )

    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "tier": user.tier,
        },
    )


@router.get("/me")
def get_me(user: CurrentUser) -> dict[str, Any]:
    """Get current user profile from JWT."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    rate = get_rate_limit_status(user)
    return {
        "id": user.get("sub"),
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture"),
        "tier": user.get("tier", "free"),
        "rate_limit": rate,
    }


@router.get("/rate-limit")
def get_user_rate_limit(user: OptionalUser) -> dict[str, Any]:
    """Get current user's rate limit status."""
    if not user:
        return {
            "tier": "anonymous",
            "daily_limit": 50,
            "used_today": 0,
            "remaining": 50,
            "cooldown_seconds": 0,
        }
    return get_rate_limit_status(user)
