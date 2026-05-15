"""Stage 9 — Human Review: video preview, QC report, approve/edit/regenerate."""

from __future__ import annotations

import logging

from backend.pipeline.stage import PipelineStage, StageContext, StageResult

logger = logging.getLogger(__name__)


class ReviewStage(PipelineStage):
    stage_number = 9
    stage_name = "Human Review"

    async def run(self, ctx: StageContext) -> StageResult:
        output: dict = {
            "status": "awaiting_review",
            "video_path": "",
            "qc_report": {},
            "export_formats": ["tiktok", "reels", "shorts"],
            "download_url": "",
        }
        errors: list[str] = []

        stage_outputs = ctx.data.get("stage_outputs", {})
        prev_output = ctx.data.get("previous_stage_output", {})
        video_path = prev_output.get("output_video") or stage_outputs.get("7", {}).get(
            "output_video", ""
        )

        if not video_path:
            errors.append("No assembled video available for review")

        gates = prev_output.get("gates") or stage_outputs.get("8", {}).get("gates", {})
        output["qc_report"] = {
            "lip_sync_quality": gates.get("lip_sync_quality", "Unknown"),
            "voice_match": gates.get("voice_match", "Unknown"),
            "visual_quality": gates.get("visual_quality", "Unknown"),
            "overall_realism": gates.get("overall_realism", "Unknown"),
            "caption_quality": gates.get("caption_quality", "Unknown"),
            "cta_present": gates.get("cta_present", False),
            "video_path": video_path,
            "segment_count": gates.get("segment_count", 0),
        }
        output["video_path"] = video_path
        output["download_url"] = f"/api/v1/projects/{ctx.project_id}/download"

        if errors:
            return StageResult.failure(9, errors, output)
        return StageResult.success(9, output)
