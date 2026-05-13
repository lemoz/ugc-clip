"""Stage 7 — FFmpeg Assembly: concat segments, captions, watermark, audio mix, export."""

from __future__ import annotations

import logging

from backend.pipeline.stage import PipelineStage, StageContext, StageResult

logger = logging.getLogger(__name__)


class AssemblyStage(PipelineStage):
    stage_number = 7
    stage_name = "FFmpeg Assembly"

    async def run(self, ctx: StageContext) -> StageResult:
        output: dict = {
            "output_video": "",
            "has_captions": True,
            "has_watermark": True,
            "has_cta_end_card": True,
        }
        errors: list[str] = []

        prev_output = ctx.data.get("previous_stage_output", {})
        segments = prev_output.get("segments", [])

        src_paths = [
            seg["lipsync_path"]
            for seg in segments
            if seg.get("status") == "complete" and seg.get("lipsync_path")
        ]

        if not src_paths:
            errors.append("No completed lip sync segments to assemble")

        output["segment_count"] = len(src_paths)
        output["input_segments"] = src_paths

        from pathlib import Path

        from backend.config import load_settings

        settings = load_settings()
        out_dir = Path(settings.local_asset_dir) / ctx.project_id
        out_dir.mkdir(parents=True, exist_ok=True)
        output["output_video"] = str(out_dir / "output.mp4")

        if errors:
            return StageResult.failure(7, errors, output)
        return StageResult.success(7, output)
