import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    dev_user: str | None = Header(default=None, alias="X-User-Id"),
    settings: Settings = Depends(get_settings),
) -> str:
    """Decode a JWT from Authorization: Bearer <token>; dev fallback to X-User-Id when no secret is set."""
    if settings.auth_secret:
        token = _extract_bearer(authorization)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )
        try:
            expected_aud = settings.auth_audience or None
            required_claims = ["sub"] + (["aud"] if expected_aud else [])
            claims = jwt.decode(
                token,
                settings.auth_secret,
                algorithms=[settings.auth_algorithm],
                audience=expected_aud,
                options={"require": required_claims},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            ) from exc
        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing sub claim")
        return str(user_id)

    # Development fallback: allow header-based user injection when no secret configured.
    if dev_user:
        return dev_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def _extract_bearer(header: str | None) -> str | None:
    if not header:
        return None
    parts = header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]
