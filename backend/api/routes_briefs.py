"""Brief and template API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.config import load_settings
from backend.models.base import get_session
from backend.models.project import Brief
from backend.models.user import User
from backend.pipeline.templates import find_template, load_all_templates

router = APIRouter(prefix="/api/v1")


class BriefCreate(BaseModel):
    template_slug: str = "product-review"
    title: str = "Untitled Brief"
    topic: str | None = None
    product_name: str | None = None
    key_claims: str | None = None
    call_to_action: str | None = None
    tone: str | None = None
    target_platform: str = "tiktok"
    target_audience: str | None = None
    target_duration: int = 30
    custom_notes: str | None = None


@router.get("/templates")
async def list_templates(current_user: User = Depends(get_current_user)):
    settings = load_settings()
    return load_all_templates(Path(settings.templates_dir))


@router.post("/briefs", status_code=201)
async def create_brief(
    body: BriefCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    settings = load_settings()
    template = find_template(Path(settings.templates_dir), body.template_slug)
    default_tone = template.get("tone", "casual") if template else "casual"
    brief = Brief(
        user_id=current_user.id,
        title=body.title,
        topic=body.topic,
        product_name=body.product_name,
        key_claims=body.key_claims,
        call_to_action=body.call_to_action,
        tone=body.tone or default_tone,
        target_platform=body.target_platform,
        target_audience=body.target_audience,
        target_duration=body.target_duration,
        custom_notes=body.custom_notes,
    )
    session.add(brief)
    await session.commit()
    return {"id": brief.id, "template_slug": body.template_slug, "title": brief.title}


@router.get("/briefs/{brief_id}")
async def get_brief(
    brief_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Brief).where(Brief.id == brief_id, Brief.user_id == current_user.id)
    )
    brief = result.scalar_one_or_none()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief
