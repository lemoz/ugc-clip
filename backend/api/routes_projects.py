"""Project API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.models.base import get_session
from backend.models.persona import Persona
from backend.models.project import Project
from backend.models.user import User

router = APIRouter(prefix="/api/v1/projects")


class ProjectCreate(BaseModel):
    persona_id: str
    brief_id: str | None = None
    name: str = "Untitled"
    platform: str = "tiktok"


class ProjectResponse(BaseModel):
    id: str
    persona_id: str
    brief_id: str | None = None
    name: str
    status: str
    stage: int
    error: str | None = None
    cost_usd: float = 0.0


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    persona_result = await session.execute(
        select(Persona).where(
            Persona.id == body.persona_id, Persona.user_id == current_user.id
        )
    )
    if not persona_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Persona not found")

    project = Project(
        user_id=current_user.id,
        persona_id=body.persona_id,
        brief_id=body.brief_id,
        name=body.name,
        platform=body.platform,
    )
    session.add(project)
    await session.commit()
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
