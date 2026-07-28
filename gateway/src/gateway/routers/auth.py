"""POST /v1/auth/token — exchange a valid API key for a short-lived JWT."""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_access_token
from ..db import get_db
from ..schemas import TokenRequest, TokenResponse
from ..settings import Settings

from models import ApiKey, User  # noqa: E402 (migrations on sys.path via package __init__)

settings = Settings()
router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    body: TokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    hashed = hashlib.sha256(body.api_key.encode()).hexdigest()

    result = await db.execute(select(ApiKey).where(ApiKey.hashed_key == hashed))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token = create_access_token(
        user_id=str(user.id),
        org_id=str(user.org_id),
        scopes=api_key.scopes,
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )
