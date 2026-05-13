"""Job CRUD operations (ported from GOV CLIP's db.ts)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Job as JobModel
from backend.models import Project


async def create_job(
    session: AsyncSession,
    *,
    job_type: str,
    project_id: str | None = None,
    segment_id: str | None = None,
    persona_id: str | None = None,
    input_data: dict[str, Any] | None = None,
) -> JobModel:
    job = JobModel(
        job_type=job_type,
        project_id=project_id,
        segment_id=segment_id,
        persona_id=persona_id,
        input_json=json.dumps(input_data) if input_data else None,
    )
    session.add(job)
    await session.commit()
    return job


async def get_job(session: AsyncSession, job_id: str) -> JobModel | None:
    result = await session.execute(select(JobModel).where(JobModel.id == job_id))
    return result.scalar_one_or_none()


async def claim_next_job(
    session: AsyncSession,
    job_types: list[str],
    concurrency: dict[str, int] | None = None,
) -> JobModel | None:
    currently_running = await session.execute(
        select(JobModel.job_type)
        .where(
            JobModel.status == "running",
            JobModel.job_type.in_(job_types),
        )
    )
    running_counts: dict[str, int] = {}
    for row in currently_running:
        running_counts[row[0]] = running_counts.get(row[0], 0) + 1

    for jt in job_types:
        max_concurrent = (concurrency or {}).get(jt, 3)
        if running_counts.get(jt, 0) >= max_concurrent:
            job_types = [t for t in job_types if t != jt]

    if not job_types:
        return None

    result = await session.execute(
        select(JobModel)
        .where(
            JobModel.status == "queued",
            JobModel.job_type.in_(job_types),
            JobModel.attempts < JobModel.max_attempts,
        )
        .order_by(JobModel.created_at.asc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if job is None:
        return None

    job.status = "running"
    job.progress = None
    job.attempts += 1
    job.started_at = datetime.now(UTC)
    await session.commit()
    return job


async def update_job_progress(session: AsyncSession, job_id: str, progress: str) -> None:
    stmt = update(JobModel).where(JobModel.id == job_id).values(progress=progress)
    await session.execute(stmt)
    await session.commit()


async def complete_job(session: AsyncSession, job_id: str, output_data: dict[str, Any]) -> None:
    stmt = (
        update(JobModel)
        .where(JobModel.id == job_id)
        .values(
            status="completed",
            output_json=json.dumps(output_data),
            error=None,
            completed_at=datetime.now(UTC),
        )
    )
    await session.execute(stmt)
    await session.commit()


async def fail_job(session: AsyncSession, job_id: str, error: str) -> None:
    job = await get_job(session, job_id)
    if job is None:
        return

    if job.attempts < job.max_attempts:
        job.status = "queued"
        job.error = error
    else:
        job.status = "failed"
        job.error = error
        job.completed_at = datetime.now(UTC)
    await session.commit()


async def update_project_state(
    session: AsyncSession,
    project_id: str,
    status: str,
    error: str | None = None,
) -> None:
    stmt = (
        update(Project)
        .where(Project.id == project_id)
        .values(status=status, error=error)
    )
    await session.execute(stmt)
    await session.commit()
