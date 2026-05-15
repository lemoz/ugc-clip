"""Default pipeline wiring for the UGC generation path."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Brief, Persona, Project, SourceClip, VoiceProfile
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.pipeline.stages.stage_0_onboard import OnboardStage
from backend.pipeline.stages.stage_1_brief import BriefStage
from backend.pipeline.stages.stage_2_artifacts import ArtifactsStage
from backend.pipeline.stages.stage_3_pregate import PreGateStage
from backend.pipeline.stages.stage_4_anchors import VisualAnchorsStage
from backend.pipeline.stages.stage_5_segments import SegmentGenerationStage
from backend.pipeline.stages.stage_6_audio import AudioMixStage
from backend.pipeline.stages.stage_7_assembly import AssemblyStage
from backend.pipeline.stages.stage_8_postgate import PostGateStage
from backend.pipeline.stages.stage_9_review import ReviewStage


def build_default_orchestrator() -> PipelineOrchestrator:
    return PipelineOrchestrator(
        [
            OnboardStage(),
            BriefStage(),
            ArtifactsStage(),
            PreGateStage(),
            VisualAnchorsStage(),
            SegmentGenerationStage(),
            AudioMixStage(),
            AssemblyStage(),
            PostGateStage(),
            ReviewStage(),
        ]
    )


async def build_project_context(
    session: AsyncSession,
    project: Project,
    *,
    template_slug: str = "product-review",
) -> dict:
    result = await session.execute(
        select(Persona).where(Persona.id == project.persona_id, Persona.user_id == project.user_id)
    )
    persona = result.scalar_one()

    brief_data = {}
    if project.brief_id:
        brief_result = await session.execute(
            select(Brief).where(Brief.id == project.brief_id, Brief.user_id == project.user_id)
        )
        brief = brief_result.scalar_one_or_none()
        if brief:
            brief_data = {
                "id": brief.id,
                "title": brief.title,
                "topic": brief.topic,
                "product_name": brief.product_name,
                "key_claims": brief.key_claims,
                "call_to_action": brief.call_to_action,
                "tone": brief.tone,
                "target_platform": brief.target_platform,
                "target_audience": brief.target_audience,
                "target_duration": brief.target_duration,
                "custom_notes": brief.custom_notes,
            }

    clip = None
    if project.source_clip_id:
        clip_result = await session.execute(
            select(SourceClip).where(
                SourceClip.id == project.source_clip_id,
                SourceClip.persona_id == project.persona_id,
            )
        )
        clip = clip_result.scalar_one_or_none()
    if clip is None:
        clip_result = await session.execute(
            select(SourceClip)
            .where(SourceClip.persona_id == project.persona_id, SourceClip.media_type == "video")
            .order_by(SourceClip.created_at.desc())
            .limit(1)
        )
        clip = clip_result.scalar_one_or_none()

    voice_result = await session.execute(
        select(VoiceProfile).where(VoiceProfile.persona_id == project.persona_id)
    )
    voice = voice_result.scalar_one_or_none()

    context = {
        "persona_name": persona.display_name,
        "template_slug": template_slug,
        "brief_id": project.brief_id,
        "brief": brief_data,
    }

    if clip:
        context["source_clip_id"] = clip.id
        context["source_clip"] = {
            "id": clip.id,
            "file_path": clip.file_path,
            "source_url": clip.source_url,
            "source_type": clip.source_type,
            "media_type": clip.media_type,
        }
        context["clip_path"] = clip.file_path

    if voice:
        context["voice_profile"] = {
            "id": voice.id,
            "prompt_audio_path": voice.prompt_audio_path,
            "prompt_text": voice.prompt_text,
            "sample_duration": voice.sample_duration,
            "quality_score": voice.quality_score,
        }
        context["voice_path"] = voice.prompt_audio_path
        context["voice_text"] = voice.prompt_text

    return context
