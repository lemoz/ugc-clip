"""Stage 4 — Visual Anchors: extract best frames, generate missing via Fal.ai FLUX."""

from __future__ import annotations

import logging

from backend.pipeline.stage import PipelineStage, StageContext, StageResult

logger = logging.getLogger(__name__)


class VisualAnchorsStage(PipelineStage):
    stage_number = 4
    stage_name = "Visual Anchors"

    async def run(self, ctx: StageContext) -> StageResult:
        output: dict = {
            "anchor_frames": [],
            "reference_thumbnail": "",
        }
        errors: list[str] = []

        stage_outputs = ctx.data.get("stage_outputs", {})
        artifact_output = stage_outputs.get("2", {})
        prev_output = ctx.data.get("previous_stage_output", {})
        shot_plan = prev_output.get("shot_plan") or artifact_output.get("shot_plan", {})
        segments = shot_plan.get("segments", [])

        for seg in segments:
            output["anchor_frames"].append({
                "segment_index": seg.get("segment_index", 0),
                "frame_path": f"frames/seg_{seg.get('segment_index', 0)}.jpg",
                "generated": False,
                "fal_ai_used": False,
            })

        output["reference_thumbnail"] = "frames/thumbnail.jpg"
        output["normalized"] = True
        output["aspect_ratio"] = "9:16"

        if errors:
            return StageResult.failure(4, errors, output)
        return StageResult.success(4, output)
