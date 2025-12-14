from __future__ import annotations

from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.config import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    user_id: str
    expires_in_minutes: int = 60


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Simple demo login that signs a JWT using the configured secret.

    Not for production use; replace with real identity provider.
    """
    if not settings.auth_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth secret not configured on server.",
        )

    exp = datetime.utcnow() + timedelta(minutes=request.expires_in_minutes)
    payload = {"sub": request.user_id, "exp": exp}
    if settings.auth_audience:
        payload["aud"] = settings.auth_audience

    token = jwt.encode(payload, settings.auth_secret, algorithm=settings.auth_algorithm)
    return TokenResponse(access_token=token)
