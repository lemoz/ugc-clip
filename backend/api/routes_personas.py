"""Persona API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.models.base import get_session
from backend.models.persona import Persona
from backend.models.user import User

router = APIRouter(prefix="/api/v1/personas")


class PersonaCreate(BaseModel):
    name: str
    display_name: str | None = None
    bio: str | None = None


class PersonaResponse(BaseModel):
    id: str
    name: str
    display_name: str
    verification_status: str
    bio: str | None = None
    avatar_path: str | None = None


@router.get("", response_model=list[PersonaResponse])
async def list_personas(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Persona).where(Persona.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("", response_model=PersonaResponse, status_code=201)
async def create_persona(
    body: PersonaCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    persona = Persona(
        user_id=current_user.id,
        name=body.name,
        display_name=body.display_name or body.name,
        bio=body.bio,
    )
    session.add(persona)
    await session.commit()
    return persona


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Persona).where(
            Persona.id == persona_id, Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona
