from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import (
    Asset,
    Base,
    Brief,
    EvaluationResult,
    IdentityVerification,
    Job,
    Persona,
    Project,
    Segment,
    SourceClip,
    Template,
    User,
    VoiceProfile,
)

TEST_DB = "sqlite+aiosqlite:///data/test_ugc_clip.db"


async def _flush(session: AsyncSession) -> None:
    await session.flush()


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


async def _create_user(session: AsyncSession, email: str) -> User:
    user = User(email=email, password_hash="h", display_name="U")
    session.add(user)
    await session.flush()
    return user


@pytest.mark.asyncio
async def test_user_crud(session: AsyncSession):
    user = User(email="test@example.com", password_hash="hash", display_name="Test User")
    session.add(user)
    await session.commit()

    result = await session.execute(select(User).where(User.email == "test@example.com"))
    fetched = result.scalar_one()
    assert fetched.display_name == "Test User"
    assert fetched.tier == "free"


@pytest.mark.asyncio
async def test_persona_with_clips_and_voice(session: AsyncSession):
    user = await _create_user(session, "p2@test.com")

    persona = Persona(user_id=user.id, name="My Persona", display_name="My Persona")
    session.add(persona)
    await session.flush()

    clip = SourceClip(
        persona_id=persona.id,
        file_path="/tmp/clip.mp4",
        source_type="upload",
        overall_score=0.85,
    )
    session.add(clip)

    voice = VoiceProfile(
        persona_id=persona.id,
        prompt_audio_path="/tmp/voice.wav",
        sample_duration=15.0,
    )
    session.add(voice)
    await session.commit()

    result = await session.execute(select(SourceClip).where(SourceClip.persona_id == persona.id))
    clips = result.scalars().all()
    assert len(clips) == 1
    assert clips[0].overall_score == 0.85

    result = await session.execute(
        select(VoiceProfile).where(VoiceProfile.persona_id == persona.id)
    )
    vp = result.scalar_one()
    assert vp.sample_duration == 15.0


@pytest.mark.asyncio
async def test_project_with_segments(session: AsyncSession):
    user = await _create_user(session, "p3@test.com")
    persona = Persona(user_id=user.id, name="P", display_name="P")
    session.add(persona)
    await session.flush()

    brief = Brief(
        user_id=user.id,
        title="Test Brief",
        tone="casual",
        target_platform="tiktok",
    )
    session.add(brief)
    await session.flush()

    project = Project(
        user_id=user.id,
        persona_id=persona.id,
        brief_id=brief.id,
        name="Test Project",
        status="draft",
    )
    session.add(project)
    await session.flush()

    seg1 = Segment(
        project_id=project.id,
        segment_index=0,
        script_text="Hello world",
    )
    seg2 = Segment(
        project_id=project.id,
        segment_index=1,
        script_text="Goodbye world",
    )
    session.add_all([seg1, seg2])
    await session.commit()

    result = await session.execute(
        select(Segment).where(Segment.project_id == project.id).order_by(Segment.segment_index)
    )
    segments = result.scalars().all()
    assert len(segments) == 2
    assert segments[0].segment_index == 0
    assert segments[1].segment_index == 1


@pytest.mark.asyncio
async def test_job_lifecycle(session: AsyncSession):
    user = await _create_user(session, "j1@test.com")
    persona = Persona(user_id=user.id, name="JP", display_name="JP")
    session.add(persona)
    await session.flush()

    project = Project(
        user_id=user.id,
        persona_id=persona.id,
        name="Job Test",
    )
    session.add(project)
    await session.flush()

    job = Job(
        project_id=project.id,
        job_type="tts",
        status="queued",
    )
    session.add(job)
    await session.commit()

    result = await session.execute(select(Job).where(Job.project_id == project.id))
    fetched = result.scalar_one()
    assert fetched.job_type == "tts"
    assert fetched.status == "queued"

    fetched.status = "running"
    await session.commit()

    result = await session.execute(select(Job).where(Job.id == job.id))
    assert result.scalar_one().status == "running"


@pytest.mark.asyncio
async def test_evaluation_result(session: AsyncSession):
    user = await _create_user(session, "e1@test.com")
    persona = Persona(user_id=user.id, name="EP", display_name="EP")
    session.add(persona)
    await session.flush()

    project = Project(
        user_id=user.id,
        persona_id=persona.id,
        name="Eval Test",
    )
    session.add(project)
    await session.flush()

    eval_result = EvaluationResult(
        project_id=project.id,
        lip_sync_quality="Good",
        voice_match="Excellent",
        overall_realism="Good",
        passed=True,
        overall_score=0.85,
    )
    session.add(eval_result)
    await session.commit()

    result = await session.execute(
        select(EvaluationResult).where(EvaluationResult.project_id == project.id)
    )
    ev = result.scalar_one()
    assert ev.passed is True
    assert ev.lip_sync_quality == "Good"
    assert ev.voice_match == "Excellent"


@pytest.mark.asyncio
async def test_template_and_brief(session: AsyncSession):
    template = Template(
        name="Product Review",
        slug="product-review",
        category="review",
        config_json='{"tone":"casual","target_duration":30}',
    )
    session.add(template)
    await session.flush()

    user = await _create_user(session, "t1@test.com")

    brief = Brief(
        user_id=user.id,
        template_id=template.id,
        title="My Review",
        tone="casual",
        product_name="Widget",
        call_to_action="Buy now",
    )
    session.add(brief)
    await session.commit()

    result = await session.execute(select(Brief).where(Brief.user_id == user.id))
    fetched = result.scalar_one()
    assert fetched.product_name == "Widget"
    assert fetched.call_to_action == "Buy now"


@pytest.mark.asyncio
async def test_identity_verification(session: AsyncSession):
    user = await _create_user(session, "v1@test.com")
    persona = Persona(user_id=user.id, name="VP", display_name="VP")
    session.add(persona)
    await session.flush()

    verification = IdentityVerification(
        persona_id=persona.id,
        provider="persona",
        provider_inquiry_id="inq_123",
        status="in_progress",
    )
    session.add(verification)
    await session.commit()

    result = await session.execute(
        select(IdentityVerification).where(IdentityVerification.persona_id == persona.id)
    )
    fetched = result.scalar_one()
    assert fetched.status == "in_progress"
    assert fetched.provider_inquiry_id == "inq_123"


@pytest.mark.asyncio
async def test_asset_with_segment(session: AsyncSession):
    user = await _create_user(session, "a1@test.com")
    persona = Persona(user_id=user.id, name="AP", display_name="AP")
    session.add(persona)
    await session.flush()

    project = Project(user_id=user.id, persona_id=persona.id, name="Asset Test")
    session.add(project)
    await session.flush()

    segment = Segment(project_id=project.id, segment_index=0, script_text="Test")
    session.add(segment)
    await session.flush()

    asset = Asset(
        project_id=project.id,
        segment_id=segment.id,
        asset_type="tts_audio",
        local_path="/tmp/audio.wav",
        duration_seconds=10.5,
    )
    session.add(asset)
    await session.commit()

    result = await session.execute(select(Asset).where(Asset.project_id == project.id))
    fetched = result.scalar_one()
    assert fetched.asset_type == "tts_audio"
    assert fetched.duration_seconds == 10.5
    assert fetched.segment_id == segment.id
