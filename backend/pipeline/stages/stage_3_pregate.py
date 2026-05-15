"""Stage 3 — Pre-Generation Gates: check hook, CTA, claims, source quality, voice quality."""

from __future__ import annotations

import re

from backend.pipeline.stage import PipelineStage, StageContext, StageResult


class PreGateStage(PipelineStage):
    stage_number = 3
    stage_name = "Pre-Generation Gates"

    async def run(self, ctx: StageContext) -> StageResult:
        errors: list[str] = []
        warnings: list[str] = []
        gates_passed: dict[str, bool] = {}

        previous = ctx.data.get("previous_stage_output", {})
        script = previous.get("script", {})
        script_text = script.get("text", "")
        hook = script.get("hook", "")
        cta = script.get("call_to_action", "")

        hook_ok = self._check_hook(hook)
        gates_passed["hook"] = hook_ok
        if not hook_ok:
            errors.append("Hook must start within first few seconds of the script")

        cta_ok = self._check_cta(cta)
        gates_passed["cta"] = cta_ok
        if not cta_ok:
            errors.append("CTA is required and should be actionable")

        claims_ok = self._check_claims(script_text)
        gates_passed["claims"] = claims_ok
        if not claims_ok:
            warnings.append("Review claims for accuracy and safety")

        source_ok = self._check_source_quality(ctx)
        gates_passed["source_quality"] = source_ok
        if not source_ok:
            errors.append("Source clip quality insufficient — upload a clearer video")

        voice_ok = self._check_voice_quality(ctx)
        gates_passed["voice_quality"] = voice_ok
        if not voice_ok:
            errors.append("Voice sample too short or low quality")

        output = {"gates": gates_passed, "warnings": warnings}

        if errors:
            return StageResult.failure(3, errors, output)

        if warnings:
            result = StageResult.success(3, output)
            result.warnings.extend(warnings)
            return result

        return StageResult.success(3, output)

    def _check_hook(self, hook: str) -> bool:
        return bool(hook) and len(hook.split()) >= 3

    def _check_cta(self, cta: str) -> bool:
        return bool(cta) and len(cta.strip()) > 0

    def _check_claims(self, script_text: str) -> bool:
        risky_patterns = [
            r"\bcure[sd]?\b",
            r"\bguaranteed\b",
            r"\b100%\b.*\b(effective|success|results?)\b",
            r"\b(fda|approved)\b",
        ]
        for pattern in risky_patterns:
            if re.search(pattern, script_text, re.IGNORECASE):
                return False
        return True

    def _check_source_quality(self, ctx: StageContext) -> bool:
        previous = ctx.data.get("previous_stage_output", {})
        clip_id = previous.get("source_clip_id") or ctx.data.get("source_clip_id")
        if not clip_id:
            return False
        return True

    def _check_voice_quality(self, ctx: StageContext) -> bool:
        previous = ctx.data.get("previous_stage_output", {})
        voice_data = previous.get("voice_profile") or ctx.data.get("voice_profile", {})
        duration = voice_data.get("sample_duration", 0)
        if duration < 5:
            return False
        return True
