"""Pipeline orchestrator — runs stages 0-9 sequentially with state persistence."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Project
from backend.pipeline.artifacts import save_artifact
from backend.pipeline.stage import (
    PipelineStage,
    StageContext,
    StageResult,
    StageStatus,
)

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(self, stages: list[PipelineStage] | None = None):
        self._stages = stages or []
        self._stage_map: dict[int, PipelineStage] = {}
        for s in self._stages:
            self._stage_map[s.stage_number] = s

    def register(self, stage: PipelineStage) -> None:
        self._stages.append(stage)
        self._stage_map[stage.stage_number] = stage
        self._stages.sort(key=lambda s: s.stage_number)

    async def run(
        self,
        session: AsyncSession,
        project_id: str,
        *,
        start_stage: int = 0,
        stop_stage: int = 9,
        context_data: dict[str, Any] | None = None,
    ) -> list[StageResult]:
        project = await self._load_project(session, project_id)
        if not project:
            return [StageResult.failure(0, [f"Project {project_id} not found"])]

        initial_data = context_data or {}
        ctx = StageContext(
            session=session,
            project_id=project.id,
            user_id=project.user_id,
            persona_id=project.persona_id,
            data={
                **initial_data,
                "stage_outputs": {},
                "previous_stage_output": {},
            },
        )

        results: list[StageResult] = []

        for stage_number in range(start_stage, stop_stage + 1):
            if stage_number not in self._stage_map:
                results.append(StageResult.skipped(stage_number, "No handler registered"))
                continue

            stage = self._stage_map[stage_number]
            logger.info("Running stage %d: %s", stage_number, stage.stage_name)

            await self._update_project_stage(session, project_id, stage_number)
            ctx.data["previous_stage_output"] = results[-1].output if results else {}

            try:
                result = await stage.run(ctx)
            except Exception as e:
                logger.exception("Stage %d failed with exception", stage_number)
                result = StageResult.failure(stage_number, [str(e)])

            results.append(result)
            ctx.data["stage_outputs"][str(stage_number)] = result.output

            await save_artifact(
                session,
                project_id=project.id,
                user_id=project.user_id,
                stage_number=stage_number,
                artifact_type=f"stage_{stage_number}_output",
                content={
                    "stage_number": stage_number,
                    "stage_name": stage.stage_name,
                    "status": result.status.name.lower(),
                    "output": result.output,
                    "errors": result.errors,
                    "warnings": result.warnings,
                },
                status=result.status.name.lower(),
            )

            if result.status == StageStatus.FAILED:
                logger.error(
                    "Stage %d failed: %s — stopping pipeline",
                    stage_number,
                    result.errors,
                )
                await self._update_project_status(session, project_id, "failed", str(result.errors))
                return results

            logger.info("Stage %d completed: %s", stage_number, result.status.name)

        final_status = "awaiting_review" if stop_stage >= 9 else "complete"
        await self._update_project_status(session, project_id, final_status)
        return results

    async def _load_project(self, session: AsyncSession, project_id: str) -> Project | None:
        result = await session.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def _update_project_stage(
        self, session: AsyncSession, project_id: str, stage: int
    ) -> None:
        project = await self._load_project(session, project_id)
        if project:
            project.stage = stage
            project.status = f"stage_{stage}"
            await session.commit()

    async def _update_project_status(
        self,
        session: AsyncSession,
        project_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        project = await self._load_project(session, project_id)
        if project:
            project.status = status
            project.error = error
            await session.commit()
