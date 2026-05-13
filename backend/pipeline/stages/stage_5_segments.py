"""Stage 5 — Segment Generation: per-segment TTS + lip sync."""

from __future__ import annotations

import logging
from pathlib import Path

from backend.config import load_settings
from backend.pipeline.lipsync.service import LipsyncService, StubLipsyncService
from backend.pipeline.stage import PipelineStage, StageContext, StageResult
from backend.pipeline.tts.service import StubTtsService, TtsService

logger = logging.getLogger(__name__)


class SegmentGenerationStage(PipelineStage):
    stage_number = 5
    stage_name = "Segment Generation"

    def __init__(
        self,
        tts_service: TtsService | None = None,
        lipsync_service: LipsyncService | None = None,
    ):
        self._tts = tts_service or StubTtsService()
        self._lipsync = lipsync_service or StubLipsyncService()

    async def run(self, ctx: StageContext) -> StageResult:
        output: dict = {"segments": []}
        errors: list[str] = []

        prev_output = ctx.data.get("previous_stage_output", {})
        script = prev_output.get("script", {})
        shot_plan = prev_output.get("shot_plan", {})
        segments_config = shot_plan.get("segments", [])

        source_clip_id = prev_output.get("source_clip_id", "")
        clip_path = self._get_source_clip_path(ctx, source_clip_id)

        voice_profile = prev_output.get("voice_profile", {})

        settings = load_settings()
        data_dir = Path(settings.data_dir)
        segments_dir = data_dir / "projects" / ctx.project_id / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)

        for seg_conf in segments_config:
            seg_index = seg_conf.get("segment_index", 0)

            seg_output_dir = segments_dir / f"seg_{seg_index}"
            seg_output_dir.mkdir(parents=True, exist_ok=True)

            try:
                logger.info(
                    "Generating segment %d/%d for project %s",
                    seg_index + 1,
                    len(segments_config),
                    ctx.project_id,
                )

                tts_result = await self._tts.generate(
                    script_text=script.get("text", ""),
                    voice_prompt_audio=voice_profile.get("prompt_audio_path", clip_path),
                    voice_prompt_text=voice_profile.get("prompt_text"),
                    output_dir=str(seg_output_dir),
                )

                lipsync_result = await self._lipsync.generate(
                    video_path=clip_path,
                    audio_path=tts_result.audio_path,
                    output_dir=str(seg_output_dir),
                )

                output["segments"].append({
                    "segment_index": seg_index,
                    "tts_path": tts_result.audio_path,
                    "tts_duration": tts_result.duration_seconds,
                    "lipsync_path": lipsync_result.video_path,
                    "lipsync_duration": lipsync_result.duration_seconds,
                    "status": "complete",
                })

            except Exception as e:
                logger.exception("Segment %d failed", seg_index)
                errors.append(f"Segment {seg_index} failed: {e}")
                output["segments"].append({
                    "segment_index": seg_index,
                    "error": str(e),
                    "status": "failed",
                })

        if errors:
            return StageResult.failure(5, errors, output)
        return StageResult.success(5, output)

    def _get_source_clip_path(self, ctx: StageContext, clip_id: str) -> str:
        settings = load_settings()
        data_dir = Path(settings.data_dir)
        default = str(data_dir / "uploads" / "video" / "default.mp4")
        return default

    async def _create_job(
        self, ctx: StageContext, job_type: str, input_data: dict
    ) -> str:
        from backend.pipeline.job_queries import create_job

        job = await create_job(
            ctx.session, job_type=job_type, project_id=ctx.project_id, input_data=input_data
        )
        return job.id
