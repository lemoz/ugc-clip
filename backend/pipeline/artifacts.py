"""Helpers for persisted pipeline JSON artifacts."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pipeline_artifact import PipelineArtifact


async def save_artifact(
    session: AsyncSession,
    *,
    project_id: str,
    user_id: str,
    stage_number: int,
    artifact_type: str,
    content: dict[str, Any],
    status: str = "created",
) -> PipelineArtifact:
    artifact = PipelineArtifact(
        project_id=project_id,
        user_id=user_id,
        stage_number=stage_number,
        artifact_type=artifact_type,
        content_json=json.dumps(content),
        status=status,
    )
    session.add(artifact)
    await session.commit()
    return artifact


async def list_artifacts(session: AsyncSession, project_id: str) -> list[PipelineArtifact]:
    result = await session.execute(
        select(PipelineArtifact)
        .where(PipelineArtifact.project_id == project_id)
        .order_by(PipelineArtifact.stage_number.asc(), PipelineArtifact.created_at.asc())
    )
    return list(result.scalars().all())


def artifact_content(artifact: PipelineArtifact) -> dict[str, Any]:
    return json.loads(artifact.content_json)
