"""API Key CRUD — generation, listing, and revocation."""

import hashlib
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthenticatedUser, get_current_user, require_scope
from ..db import get_db
from ..schemas import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse

from models import ApiKey, User  # noqa: E402

router = APIRouter(prefix="/v1/users", tags=["api-keys"])

_require_keys_write = require_scope("keys:write")


def _generate_keypair() -> tuple[str, str]:
    """Return (plaintext, sha256_hex). Plaintext is never stored."""
    plaintext = f"af-{secrets.token_hex(24)}"
    return plaintext, hashlib.sha256(plaintext.encode()).hexdigest()


def _assert_own_or_admin(user_id: UUID, current_user: AuthenticatedUser) -> None:
    if str(user_id) != current_user.user_id and current_user.user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.post(
    "/{user_id}/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    user_id: UUID,
    body: ApiKeyCreate,
    current_user: Annotated[AuthenticatedUser, Depends(_require_keys_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKeyCreatedResponse:
    _assert_own_or_admin(user_id, current_user)

    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    plaintext, hashed = _generate_keypair()
    key = ApiKey(
        user_id=user_id,
        hashed_key=hashed,
        scopes=body.scopes,
        budget_usd=body.budget_usd,
        expires_at=body.expires_at,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    return ApiKeyCreatedResponse(
        id=key.id,
        user_id=key.user_id,
        scopes=key.scopes,
        budget_usd=key.budget_usd,
        expires_at=key.expires_at,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        plaintext_key=plaintext,
    )


@router.get("/{user_id}/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ApiKeyResponse]:
    _assert_own_or_admin(user_id, current_user)
    result = await db.execute(select(ApiKey).where(ApiKey.user_id == user_id))
    return list(result.scalars().all())


@router.delete("/{user_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    user_id: UUID,
    key_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(_require_keys_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    _assert_own_or_admin(user_id, current_user)
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
    )
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    db.delete(key)
    await db.commit()
