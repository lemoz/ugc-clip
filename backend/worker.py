"""Async background job worker (ported from GOV CLIP's worker.ts).

Poll-based: checks for queued jobs every 3 seconds, claims and processes
them with per-type concurrency limits.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.base import _get_session_factory
from backend.models.job import Job as JobModel
from backend.pipeline.job_queries import (
    claim_next_job,
    complete_job,
    fail_job,
    update_project_state,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL = 3.0
DEFAULT_CONCURRENCY = {"tts": 1, "lipsync": 3, "other": 5}

JobHandler = Callable[[AsyncSession, str, str | None, str | None], Awaitable[dict]]


class JobWorker:
    def __init__(self, concurrency: dict[str, int] | None = None) -> None:
        self._concurrency = concurrency or DEFAULT_CONCURRENCY
        self._handlers: dict[str, JobHandler] = {}
        self._running = False
        self._task: asyncio.Task | None = None
        self._running_counts: dict[str, int] = {}

    def register_handler(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Job worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Job worker stopped")

    async def _poll_loop(self) -> None:
        handler_types = list(self._handlers.keys())
        batch_1 = [t for t in handler_types if t == "tts"]
        batch_2 = [t for t in handler_types if t == "lipsync"]
        batch_3 = [t for t in handler_types if t not in ("tts", "lipsync")]

        while self._running:
            for batch in (batch_1, batch_2, batch_3):
                if batch:
                    await self._poll_batch(batch)
            await asyncio.sleep(POLL_INTERVAL)

    async def _poll_batch(self, job_types: list[str]) -> None:
        factory = _get_session_factory()
        async with factory() as session:
            for jt in job_types:
                max_conc = self._concurrency.get(jt, 3)
                if self._running_counts.get(jt, 0) >= max_conc:
                    continue

                job = await claim_next_job(session, [jt], self._concurrency)
                if job is None:
                    continue

                self._running_counts[jt] = self._running_counts.get(jt, 0) + 1
                asyncio.create_task(self._process_job(session, job.id, jt))

    async def _process_job(self, session: AsyncSession, job_id: str, job_type: str) -> None:
        handler = self._handlers.get(job_type)
        try:
            if handler:
                result = await handler(session, job_id, None, None)
                await complete_job(session, job_id, result)
            else:
                raise ValueError(f"No handler for job type: {job_type}")
        except Exception:
            logger.exception("Job %s failed", job_id)
            await fail_job(session, job_id, "Job processing failed")

            result = await session.execute(
                select(JobModel).where(JobModel.id == job_id)
            )
            job_row = result.scalar_one_or_none()
            if job_row and job_row.project_id:
                await update_project_state(session, job_row.project_id, "failed")
        finally:
            self._running_counts[job_type] = max(
                0, self._running_counts.get(job_type, 1) - 1
            )


_worker: JobWorker | None = None


def get_worker() -> JobWorker:
    global _worker
    if _worker is None:
        _worker = JobWorker()
    return _worker
