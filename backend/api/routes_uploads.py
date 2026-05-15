"""Upload API routes for persona media."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.models.base import get_session
from backend.models.persona import Persona, SourceClip, VoiceProfile
from backend.models.user import User
from backend.pipeline.upload import save_upload

router = APIRouter(prefix="/api/v1/uploads")


async def _owned_persona(session: AsyncSession, user_id: str, persona_id: str) -> Persona:
    result = await session.execute(
        select(Persona).where(Persona.id == persona_id, Persona.user_id == user_id)
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona


@router.post("/video", status_code=201)
async def upload_video(
    persona_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_persona(session, current_user.id, persona_id)
    path = await save_upload(file, "video")
    clip = SourceClip(
        persona_id=persona_id,
        file_path=path,
        media_type="video",
        source_type="upload",
    )
    session.add(clip)
    await session.commit()
    return {"id": clip.id, "file_path": clip.file_path, "media_type": clip.media_type}


@router.post("/voice", status_code=201)
async def upload_voice(
    persona_id: str = Form(...),
    file: UploadFile = File(...),
    prompt_text: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_persona(session, current_user.id, persona_id)
    path = await save_upload(file, "voice")
    result = await session.execute(
        select(VoiceProfile).where(VoiceProfile.persona_id == persona_id)
    )
    profile = result.scalar_one_or_none()
    if profile:
        profile.prompt_audio_path = path
        profile.prompt_text = prompt_text
        profile.sample_duration = 15.0
    else:
        profile = VoiceProfile(
            persona_id=persona_id,
            prompt_audio_path=path,
            prompt_text=prompt_text,
            sample_duration=15.0,
        )
        session.add(profile)
    await session.commit()
    return {"id": profile.id, "prompt_audio_path": profile.prompt_audio_path}
