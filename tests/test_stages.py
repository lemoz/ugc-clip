from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base, Persona, User
from backend.pipeline.stage import StageContext
from backend.pipeline.stages.stage_4_anchors import VisualAnchorsStage
from backend.pipeline.stages.stage_7_assembly import AssemblyStage
from backend.pipeline.stages.stage_8_postgate import PostGateStage
from backend.pipeline.stages.stage_9_review import ReviewStage

TEST_DB = "sqlite+aiosqlite:///data/test_stages.db"


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


async def _setup(session: AsyncSession):
    user = User(email="s@test.com", password_hash="h", display_name="S")
    session.add(user)
    await session.flush()
    persona = Persona(user_id=user.id, name="SP", display_name="SP")
    session.add(persona)
    await session.commit()
    return user, persona


@pytest.mark.asyncio
async def test_visual_anchors_stage(session: AsyncSession):
    user, persona = await _setup(session)

    ctx = StageContext(
        session=session,
        project_id="proj_va",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "shot_plan": {
                    "segments": [
                        {"segment_index": 0},
                        {"segment_index": 1},
                    ],
                },
            },
        },
    )

    stage = VisualAnchorsStage()
    result = await stage.run(ctx)
    assert result.passed
    assert len(result.output["anchor_frames"]) == 2
    assert result.output["aspect_ratio"] == "9:16"


@pytest.mark.asyncio
async def test_assembly_stage(session: AsyncSession):
    user, persona = await _setup(session)

    ctx = StageContext(
        session=session,
        project_id="proj_asm",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "segments": [
                    {
                        "segment_index": 0,
                        "lipsync_path": "/tmp/seg0.mp4",
                        "status": "complete",
                    },
                ],
            },
        },
    )

    stage = AssemblyStage()
    result = await stage.run(ctx)
    assert result.passed
    assert result.output["segment_count"] == 1


@pytest.mark.asyncio
async def test_assembly_stage_no_segments(session: AsyncSession):
    user, persona = await _setup(session)

    ctx = StageContext(
        session=session,
        project_id="proj_asm2",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {"segments": []},
        },
    )

    stage = AssemblyStage()
    result = await stage.run(ctx)
    assert not result.passed


@pytest.mark.asyncio
async def test_postgate_stage(session: AsyncSession):
    user, persona = await _setup(session)

    ctx = StageContext(
        session=session,
        project_id="proj_pg",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "segments": [
                    {"segment_index": 0, "status": "complete"},
                ],
            },
        },
    )

    stage = PostGateStage()
    result = await stage.run(ctx)
    assert result.passed
    gates = result.output["gates"]
    assert gates["segment_count"] == 1
    assert gates["cta_present"] is True


@pytest.mark.asyncio
async def test_postgate_stage_no_completed_segments(session: AsyncSession):
    user, persona = await _setup(session)

    ctx = StageContext(
        session=session,
        project_id="proj_pg2",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {"segments": []},
        },
    )

    stage = PostGateStage()
    result = await stage.run(ctx)
    assert not result.passed


@pytest.mark.asyncio
async def test_review_stage(session: AsyncSession):
    user, persona = await _setup(session)

    ctx = StageContext(
        session=session,
        project_id="proj_rev",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "output_video": "/tmp/output.mp4",
                "gates": {
                    "lip_sync_quality": "Good",
                    "voice_match": "Good",
                    "visual_quality": "Good",
                    "overall_realism": "Good",
                    "caption_quality": "Good",
                    "cta_present": True,
                    "segment_count": 2,
                },
            },
        },
    )

    stage = ReviewStage()
    result = await stage.run(ctx)
    assert result.passed
    assert result.output["status"] == "awaiting_review"
    assert result.output["qc_report"]["voice_match"] == "Good"
    assert "download_url" in result.output


@pytest.mark.asyncio
async def test_review_stage_no_video(session: AsyncSession):
    user, persona = await _setup(session)

    ctx = StageContext(
        session=session,
        project_id="proj_rev2",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {},
        },
    )

    stage = ReviewStage()
    result = await stage.run(ctx)
    assert not result.passed
