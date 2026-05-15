"""Stage 0 — Onboarding & Upload: save uploads, create persona, extract voice."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.persona import Persona, SourceClip, VoiceProfile
from backend.pipeline.stage import PipelineStage, StageContext, StageResult


class OnboardStage(PipelineStage):
    stage_number = 0
    stage_name = "Onboarding & Verification"

    async def run(self, ctx: StageContext) -> StageResult:
        output: dict = {}
        errors: list[str] = []

        persona = await self._ensure_persona(ctx.session, ctx)
        output["persona_id"] = persona.id

        clip_path = ctx.data.get("clip_path")
        if clip_path:
            try:
                clip = await self._create_source_clip(
                    ctx.session, persona.id, clip_path, ctx.data.get("source_url")
                )
                output["source_clip_id"] = clip.id
                output["source_clip"] = {
                    "id": clip.id,
                    "file_path": clip.file_path,
                    "source_url": clip.source_url,
                    "source_type": clip.source_type,
                }
            except Exception as e:
                errors.append(f"Clip creation failed: {e}")

        voice_path = ctx.data.get("voice_path")
        if voice_path:
            try:
                profile = await self._create_voice_profile(
                    ctx.session, persona.id, voice_path, ctx.data.get("voice_text")
                )
                output["voice_profile_id"] = profile.id
                output["voice_profile"] = {
                    "id": profile.id,
                    "prompt_audio_path": profile.prompt_audio_path,
                    "prompt_text": profile.prompt_text,
                    "sample_duration": profile.sample_duration,
                    "quality_score": profile.quality_score,
                }
            except Exception as e:
                errors.append(f"Voice profile creation failed: {e}")

        if errors:
            return StageResult.failure(0, errors, output)

        return StageResult.success(0, output)

    async def _ensure_persona(self, session: AsyncSession, ctx: StageContext) -> Persona:
        result = await session.execute(
            select(Persona).where(Persona.id == ctx.persona_id, Persona.user_id == ctx.user_id)
        )
        persona = result.scalar_one_or_none()
        if persona:
            return persona

        persona_name = ctx.data.get("persona_name", "Default Persona")
        persona = Persona(
            user_id=ctx.user_id,
            name=persona_name,
            display_name=persona_name,
        )
        session.add(persona)
        await session.commit()
        return persona

    async def _create_source_clip(
        self,
        session: AsyncSession,
        persona_id: str,
        file_path: str,
        source_url: str | None = None,
    ) -> SourceClip:
        source_type = "url_import" if source_url else "upload"
        existing = await session.execute(
            select(SourceClip).where(
                SourceClip.persona_id == persona_id,
                SourceClip.file_path == file_path,
            )
        )
        existing_clip = existing.scalar_one_or_none()
        if existing_clip:
            return existing_clip

        clip = SourceClip(
            persona_id=persona_id,
            file_path=file_path,
            source_type=source_type,
            source_url=source_url,
        )
        session.add(clip)
        await session.commit()
        return clip

    async def _create_voice_profile(
        self,
        session: AsyncSession,
        persona_id: str,
        audio_path: str,
        prompt_text: str | None = None,
    ) -> VoiceProfile:
        duration = 0.0
        try:
            duration = float(self._get_audio_duration(audio_path))
        except Exception:
            pass

        existing = await session.execute(
            select(VoiceProfile).where(VoiceProfile.persona_id == persona_id)
        )
        profile = existing.scalar_one_or_none()
        if profile:
            profile.prompt_audio_path = audio_path
            profile.prompt_text = prompt_text
            profile.sample_duration = duration
            await session.commit()
            return profile

        profile = VoiceProfile(
            persona_id=persona_id,
            prompt_audio_path=audio_path,
            prompt_text=prompt_text,
            sample_duration=duration,
        )
        session.add(profile)
        await session.commit()
        return profile

    @staticmethod
    def _get_audio_duration(path: str) -> float:
        p = Path(path)
        if not p.exists():
            return 0.0
        try:
            import subprocess

            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(p),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0
