"""Org and Project CRUD endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthenticatedUser, get_current_user, require_scope
from ..db import get_db
from ..schemas import OrgCreate, OrgResponse, ProjectCreate, ProjectResponse

from models import Organization, Project  # noqa: E402

router = APIRouter(prefix="/v1/orgs", tags=["orgs"])

_require_org_admin = require_scope("org:admin")


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

@router.get("", response_model=list[OrgResponse])
async def list_orgs(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OrgResponse]:
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.user.org_id)
    )
    return list(result.scalars().all())


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org(
    body: OrgCreate,
    current_user: Annotated[AuthenticatedUser, Depends(_require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrgResponse:
    org = Organization(name=body.name, slug=body.slug)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


# ---------------------------------------------------------------------------
# Projects (scoped under an org)
# ---------------------------------------------------------------------------

@router.get("/{org_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    org_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ProjectResponse]:
    if str(org_id) != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    result = await db.execute(select(Project).where(Project.org_id == org_id))
    return list(result.scalars().all())


@router.post(
    "/{org_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    org_id: UUID,
    body: ProjectCreate,
    current_user: Annotated[AuthenticatedUser, Depends(_require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    if str(org_id) != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    project = Project(org_id=org_id, name=body.name, settings_json=body.settings_json)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{org_id}/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    org_id: UUID,
    project_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(_require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    if str(org_id) != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.org_id == org_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    db.delete(project)
    await db.commit()
