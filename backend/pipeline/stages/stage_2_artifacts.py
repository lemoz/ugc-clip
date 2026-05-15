"""Stage 2 — Structured Artifacts: generate script, style card, shot plan, voice profile."""

from __future__ import annotations

from backend.pipeline.stage import PipelineStage, StageContext, StageResult


class ArtifactsStage(PipelineStage):
    stage_number = 2
    stage_name = "Structured Artifacts"

    async def run(self, ctx: StageContext) -> StageResult:
        output: dict = {
            "script": {},
            "style_card": {},
            "shot_plan": {},
            "voice_profile": {},
        }
        errors: list[str] = []

        previous = ctx.data.get("previous_stage_output", {})
        brief_data = previous.get("brief") or ctx.data.get("brief", {})
        template_def = previous.get("template", {})

        script = await self._generate_script(brief_data, template_def)
        output["script"] = script

        style_card = self._generate_style_card(brief_data, template_def)
        output["style_card"] = style_card

        shot_plan = self._generate_shot_plan(script, template_def)
        output["shot_plan"] = shot_plan

        voice_data = ctx.data.get("voice_profile", {})
        output["voice_profile"] = voice_data
        if ctx.data.get("source_clip_id"):
            output["source_clip_id"] = ctx.data["source_clip_id"]

        if errors:
            return StageResult.failure(2, errors, output)
        return StageResult.success(2, output)

    async def _generate_script(
        self,
        brief_data: dict,
        template_def: dict,
    ) -> dict:
        product_name = brief_data.get("product_name", "[product]")
        tone = brief_data.get("tone", "casual")
        cta = brief_data.get("call_to_action") or "Check the link in my bio"
        topic = brief_data.get("topic", "")

        hook = f"I've been using {product_name} for the past month and I have to be honest..."
        body = f"{topic} This product genuinely surprised me. " \
               "The quality exceeded my expectations."
        full_script = f"{hook} {body} {cta}"
        words = full_script.split()
        word_count = len(words)

        return {
            "text": full_script,
            "word_count": word_count,
            "hook": hook,
            "body": body,
            "call_to_action": cta,
            "duration_estimate": int(word_count / 2.5),
            "tone": tone,
        }

    def _generate_style_card(self, brief_data: dict, template_def: dict) -> dict:
        return {
            "energy": "medium",
            "lighting": "natural",
            "background": "clean, uncluttered",
            "wardrobe": "casual",
            "tone": brief_data.get("tone", "casual"),
            "camera_distance": "close-up to medium",
            "pace": "natural, conversational",
        }

    def _generate_shot_plan(self, script: dict, template_def: dict) -> dict:
        word_count = script.get("word_count", 80)
        segment_count = max(1, word_count // 25)
        segments = []
        for i in range(segment_count):
            segments.append({
                "segment_index": i,
                "shot_type": "close-up" if i == 0 else "medium",
                "focus": "face" if i % 2 == 0 else "hands/product",
                "duration_estimate": 10,
            })
        return {"segments": segments, "total_segments": segment_count}
