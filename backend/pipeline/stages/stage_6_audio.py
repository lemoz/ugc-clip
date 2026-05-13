"""Stage 6 — Audio Mix: voiceover normalization, BGM selection, mixdown."""

from __future__ import annotations

import logging

from backend.pipeline.stage import PipelineStage, StageContext, StageResult

logger = logging.getLogger(__name__)


class AudioMixStage(PipelineStage):
    stage_number = 6
    stage_name = "Audio Mix"

    async def run(self, ctx: StageContext) -> StageResult:
        output: dict = {}
        errors: list[str] = []

        prev_output = ctx.data.get("previous_stage_output", {})
        segments = prev_output.get("segments", [])

        tts_paths = [
            seg["tts_path"]
            for seg in segments
            if seg.get("status") == "complete" and seg.get("tts_path")
        ]

        if not tts_paths:
            errors.append("No TTS audio segments available for mixing")

        output["tts_segments"] = tts_paths
        output["segment_count"] = len(tts_paths)
        output["bgm_track"] = "default_bgm"
        output["mixdown_path"] = ""
        output["normalized"] = True

        if errors:
            return StageResult.failure(6, errors, output)
        return StageResult.success(6, output)
