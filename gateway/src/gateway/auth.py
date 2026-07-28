"""Authentication helpers: JWT issuance/validation, API key verification, scope enforcement."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .settings import Settings

# models imported after __init__.py adds migrations/ to sys.path
from models import ApiKey, User  # noqa: E402

settings = Settings()
_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(user_id: str, org_id: str, scopes: list[str]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "org_id": org_id, "scopes": scopes, "exp": expire},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )  # PyJWT >= 2.0 returns str directly; exp accepts timezone-aware datetime


# ---------------------------------------------------------------------------
# Authenticated-user value object
# ---------------------------------------------------------------------------

@dataclass
class AuthenticatedUser:
    user: User
    scopes: list[str] = field(default_factory=list)

    @property
    def user_id(self) -> str:
        return str(self.user.id)

    @property
    def org_id(self) -> str:
        return str(self.user.org_id)


# ---------------------------------------------------------------------------
# Core dependency: get_current_user
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials

    # --- Try JWT first (no DB hit when the token is valid) ---
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return AuthenticatedUser(user=user, scopes=payload.get("scopes", []))
    except jwt.InvalidTokenError:
        pass

    # --- Fall back to API key lookup ---
    hashed = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(select(ApiKey).where(ApiKey.hashed_key == hashed))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired")

    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return AuthenticatedUser(user=user, scopes=api_key.scopes)


# ---------------------------------------------------------------------------
# Scope enforcement factory
# ---------------------------------------------------------------------------

def require_scope(*required: str):
    """Returns a FastAPI dependency that passes only if the user holds at least one required scope.

    Wildcard scope ``*`` always passes.
    """
    async def _check(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if "*" in current_user.scopes:
            return current_user
        for s in required:
            if s in current_user.scopes:
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required scope: {' | '.join(required)}",
        )
    return _check
