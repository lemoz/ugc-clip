"""Stage 1 — Content Brief: load UGC template, define product/CTA/tone."""

from __future__ import annotations

from pathlib import Path

from backend.config import load_settings
from backend.models import Brief
from backend.pipeline.stage import PipelineStage, StageContext, StageResult
from backend.pipeline.templates import find_template


class BriefStage(PipelineStage):
    stage_number = 1
    stage_name = "Content Brief"

    async def run(self, ctx: StageContext) -> StageResult:
        output: dict = {}
        errors: list[str] = []

        template_slug = ctx.data.get("template_slug", "product-review")
        settings = load_settings()
        templates_dir = Path(settings.templates_dir)

        template_def = find_template(templates_dir, template_slug)
        if template_def:
            output["template"] = template_def

        brief_data = ctx.data.get("brief", {})
        default_tone = template_def.get("tone", "casual") if template_def else "casual"

        brief = Brief(
            user_id=ctx.user_id,
            title=brief_data.get("title", "Untitled Brief"),
            topic=brief_data.get("topic"),
            product_name=brief_data.get("product_name"),
            key_claims=brief_data.get("key_claims"),
            call_to_action=brief_data.get("call_to_action"),
            tone=brief_data.get("tone", default_tone),
            target_platform=brief_data.get("target_platform", "tiktok"),
            target_audience=brief_data.get("target_audience"),
            target_duration=brief_data.get("target_duration", 30),
            custom_notes=brief_data.get("custom_notes"),
            template_id=None,
        )

        ctx.session.add(brief)
        await ctx.session.commit()

        output["brief_id"] = brief.id
        output["template_slug"] = template_slug

        if errors:
            return StageResult.failure(1, errors, output)
        return StageResult.success(1, output)
