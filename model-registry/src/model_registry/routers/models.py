"""Model CRUD endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..schemas import ModelCreate, ModelResponse, ModelUpdate

from models import Model  # noqa: E402  (migrations/ on sys.path via __init__)

router = APIRouter(prefix="/v1/models", tags=["models"])


@router.get("", response_model=list[ModelResponse])
async def list_models(
    provider: str | None = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[ModelResponse]:
    q = select(Model)
    if provider:
        q = q.where(Model.provider == provider)
    if active_only:
        q = q.where(Model.is_active.is_(True))
    q = q.order_by(Model.provider, Model.slug)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{slug}", response_model=ModelResponse)
async def get_model(slug: str, db: AsyncSession = Depends(get_db)) -> ModelResponse:
    result = await db.execute(select(Model).where(Model.slug == slug))
    m = result.scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return m


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    body: ModelCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModelResponse:
    existing = await db.execute(select(Model).where(Model.slug == body.slug))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Model '{body.slug}' already exists")
    m = Model(**body.model_dump())
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


@router.patch("/{slug}", response_model=ModelResponse)
async def update_model(
    slug: str,
    body: ModelUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModelResponse:
    result = await db.execute(select(Model).where(Model.slug == slug))
    m = result.scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    await db.commit()
    await db.refresh(m)
    return m


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(slug: str, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
    result = await db.execute(select(Model).where(Model.slug == slug))
    m = result.scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    db.delete(m)
    await db.commit()
