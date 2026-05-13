from __future__ import annotations

import asyncio
import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base, Persona, Project, User
from backend.pipeline.job_queries import (
    claim_next_job,
    complete_job,
    create_job,
    fail_job,
    get_job,
    update_job_progress,
    update_project_state,
)
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.pipeline.stage import (
    PipelineStage,
    StageContext,
    StageResult,
    StageStatus,
)

TEST_DB = "sqlite+aiosqlite:///data/test_pipeline.db"


@pytest.fixture
async def engine():
    engine = create_async_engine(TEST_DB, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncSession:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


async def _setup_project(session: AsyncSession) -> tuple[User, Persona, Project]:
    user = User(email="pipe@test.com", password_hash="h", display_name="P")
    session.add(user)
    await session.flush()

    persona = Persona(user_id=user.id, name="P", display_name="P")
    session.add(persona)
    await session.flush()

    project = Project(
        user_id=user.id,
        persona_id=persona.id,
        name="Pipeline Test",
        status="draft",
    )
    session.add(project)
    await session.commit()
    return user, persona, project


class FakeStage(PipelineStage):
    def __init__(self, stage_number: int, should_pass: bool = True, output: dict | None = None):
        self.stage_number = stage_number
        self.stage_name = f"FakeStage{stage_number}"
        self.should_pass = should_pass
        self._output = output or {"result": f"stage_{stage_number}"}
        self.was_called = False

    async def run(self, ctx: StageContext) -> StageResult:
        self.was_called = True
        if self.should_pass:
            return StageResult.success(self.stage_number, self._output)
        return StageResult.failure(self.stage_number, [f"Stage {self.stage_number} error"])


@pytest.mark.asyncio
async def test_stage_result_success():
    result = StageResult.success(1, {"key": "val"})
    assert result.passed
    assert result.stage_number == 1
    assert result.output == {"key": "val"}


@pytest.mark.asyncio
async def test_stage_result_failure():
    result = StageResult.failure(2, ["err1", "err2"])
    assert not result.passed
    assert len(result.errors) == 2


@pytest.mark.asyncio
async def test_orchestrator_runs_stages(session: AsyncSession):
    _, _, project = await _setup_project(session)

    stage0 = FakeStage(0)
    stage1 = FakeStage(1)
    stage2 = FakeStage(2)

    orchestrator = PipelineOrchestrator([stage0, stage1, stage2])
    results = await orchestrator.run(session, project.id)

    assert len(results) == 10
    assert results[0].passed
    assert results[1].passed
    assert results[2].passed
    assert results[3].status == StageStatus.SKIPPED
    assert stage0.was_called
    assert stage1.was_called
    assert stage2.was_called


@pytest.mark.asyncio
async def test_orchestrator_stops_on_failure(session: AsyncSession):
    _, _, project = await _setup_project(session)

    stage0 = FakeStage(0)
    stage1 = FakeStage(1, should_pass=False)
    stage2 = FakeStage(2)

    orchestrator = PipelineOrchestrator([stage0, stage1, stage2])
    results = await orchestrator.run(session, project.id)

    assert len(results) == 2
    assert results[0].passed
    assert not results[1].passed
    assert stage0.was_called
    assert stage1.was_called
    assert not stage2.was_called

    result = await session.execute(select(Project).where(Project.id == project.id))
    p = result.scalar_one()
    assert p.status == "failed"


@pytest.mark.asyncio
async def test_orchestrator_skips_unregistered_stages(session: AsyncSession):
    _, _, project = await _setup_project(session)

    stage0 = FakeStage(0)
    orchestrator = PipelineOrchestrator([stage0])
    results = await orchestrator.run(session, project.id)

    assert len(results) == 10
    assert results[0].status == StageStatus.PASSED
    assert all(r.status == StageStatus.SKIPPED for r in results[1:])


@pytest.mark.asyncio
async def test_create_and_get_job(session: AsyncSession):
    job = await create_job(session, job_type="test_job", input_data={"foo": "bar"})
    assert job.id is not None

    fetched = await get_job(session, job.id)
    assert fetched is not None
    assert fetched.job_type == "test_job"
    assert json.loads(fetched.input_json) == {"foo": "bar"}


@pytest.mark.asyncio
async def test_claim_next_job(session: AsyncSession):
    await create_job(session, job_type="tts")
    await create_job(session, job_type="tts")

    job = await claim_next_job(session, ["tts"], {"tts": 1})
    assert job is not None
    assert job.status == "running"
    assert job.attempts == 1

    second = await claim_next_job(session, ["tts"], {"tts": 1})
    assert second is None


@pytest.mark.asyncio
async def test_complete_job(session: AsyncSession):
    job = await create_job(session, job_type="tts")
    job.status = "running"
    job.attempts = 1
    job.started_at = job.created_at
    await session.commit()

    await complete_job(session, job.id, {"asset_id": "a1"})

    fetched = await get_job(session, job.id)
    assert fetched.status == "completed"
    assert json.loads(fetched.output_json) == {"asset_id": "a1"}


@pytest.mark.asyncio
async def test_fail_job_retries(session: AsyncSession):
    job = await create_job(session, job_type="tts")
    job.status = "running"
    job.attempts = 1
    await session.commit()

    await fail_job(session, job.id, "TTS VM failed")

    fetched = await get_job(session, job.id)
    assert fetched.status == "queued"
    assert fetched.error == "TTS VM failed"


@pytest.mark.asyncio
async def test_fail_job_exhausted_retries(session: AsyncSession):
    job = await create_job(session, job_type="tts")
    job.status = "running"
    job.attempts = 3
    job.max_attempts = 3
    await session.commit()

    await fail_job(session, job.id, "Final failure")

    fetched = await get_job(session, job.id)
    assert fetched.status == "failed"
    assert fetched.error == "Final failure"


@pytest.mark.asyncio
async def test_update_job_progress(session: AsyncSession):
    job = await create_job(session, job_type="tts")
    await update_job_progress(session, job.id, "Creating GPU VM...")

    fetched = await get_job(session, job.id)
    assert fetched.progress == "Creating GPU VM..."


@pytest.mark.asyncio
async def test_update_project_state(session: AsyncSession):
    _, _, project = await _setup_project(session)
    await update_project_state(session, project.id, "tts_running", None)
    await session.refresh(project)
    assert project.status == "tts_running"


class TestJobWorker:
    @pytest.mark.asyncio
    async def test_register_and_start(self, session: AsyncSession):
        from backend.worker import JobWorker

        worker = JobWorker()

        async def dummy_handler(s, job_id, proj_id, seg_id):
            return {"ok": True}

        async def noop_poll(types):
            pass

        worker.register_handler("test_job", dummy_handler)

        await create_job(session, job_type="test_job")

        worker._poll_batch = noop_poll
        await worker.start()
        await asyncio.sleep(0.1)
        await worker.stop()

        assert "test_job" in worker._handlers
