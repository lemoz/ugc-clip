from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base, Brief, Persona, User
from backend.pipeline.stage import StageContext
from backend.pipeline.stages.stage_1_brief import BriefStage
from backend.pipeline.stages.stage_2_artifacts import ArtifactsStage
from backend.pipeline.stages.stage_3_pregate import PreGateStage
from backend.pipeline.templates import find_template, load_all_templates

TEST_DB = "sqlite+aiosqlite:///data/test_briefs.db"


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


async def _setup_user(session: AsyncSession) -> tuple[User, Persona]:
    user = User(email="b@test.com", password_hash="h", display_name="B")
    session.add(user)
    await session.flush()
    persona = Persona(user_id=user.id, name="BP", display_name="BP")
    session.add(persona)
    await session.commit()
    return user, persona


@pytest.mark.asyncio
async def test_template_loading():
    templates_dir = Path("templates")
    templates = load_all_templates(templates_dir)
    assert len(templates) >= 1
    slugs = {t["slug"] for t in templates}
    assert "product-review" in slugs


@pytest.mark.asyncio
async def test_find_template():
    templates_dir = Path("templates")
    tmpl = find_template(templates_dir, "product-review")
    assert tmpl is not None
    assert tmpl["name"] == "Product Review"

    not_found = find_template(templates_dir, "nonexistent")
    assert not_found is None


@pytest.mark.asyncio
async def test_brief_stage(session: AsyncSession):
    user, persona = await _setup_user(session)

    stage = BriefStage()
    ctx = StageContext(
        session=session,
        project_id="proj_b",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "template_slug": "product-review",
            "brief": {
                "title": "My Product Review",
                "product_name": "Awesome Widget",
                "call_to_action": "Try it today!",
                "tone": "excited",
            },
        },
    )

    result = await stage.run(ctx)
    assert result.passed
    assert result.output["template_slug"] == "product-review"
    assert "template" in result.output

    brief_id = result.output["brief_id"]
    result_db = await session.execute(select(Brief).where(Brief.id == brief_id))
    brief = result_db.scalar_one()
    assert brief.product_name == "Awesome Widget"
    assert brief.call_to_action == "Try it today!"


@pytest.mark.asyncio
async def test_artifacts_stage(session: AsyncSession):
    user, persona = await _setup_user(session)

    ctx = StageContext(
        session=session,
        project_id="proj_b",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "brief": {
                "product_name": "Awesome Widget",
                "call_to_action": "Try it today!",
                "tone": "excited",
                "topic": "I found the best gadget",
            },
            "previous_stage_output": {
                "template": {
                    "narrative_requirements": ["Hook must start early"],
                    "script_structure": {
                        "hook": "Grab attention",
                        "body": "Share experience",
                        "cta": "Clear CTA",
                    },
                }
            },
            "voice_profile": {},
        },
    )

    stage = ArtifactsStage()
    result = await stage.run(ctx)
    assert result.passed

    script = result.output["script"]
    assert script["word_count"] > 10
    assert "Awesome Widget" in script["text"]
    assert script["call_to_action"] == "Try it today!"

    style_card = result.output["style_card"]
    assert style_card["tone"] == "excited"

    shot_plan = result.output["shot_plan"]
    assert shot_plan["total_segments"] >= 1


@pytest.mark.asyncio
async def test_pregate_stage_passes(session: AsyncSession):
    user, persona = await _setup_user(session)

    ctx = StageContext(
        session=session,
        project_id="proj_b",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "script": {
                    "text": "I love this product. It's amazing. Buy it now!",
                    "hook": "I love this product",
                    "call_to_action": "Buy it now!",
                },
                "source_clip_id": "clip_123",
                "voice_profile": {"sample_duration": 15.0},
            },
        },
    )

    stage = PreGateStage()
    result = await stage.run(ctx)
    assert result.passed
    gates = result.output["gates"]
    assert gates["hook"] is True
    assert gates["cta"] is True
    assert gates["source_quality"] is True
    assert gates["voice_quality"] is True


@pytest.mark.asyncio
async def test_pregate_stage_fails_risky_claims(session: AsyncSession):
    user, persona = await _setup_user(session)

    ctx = StageContext(
        session=session,
        project_id="proj_b",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "script": {
                    "text": "This supplement cures everything! Guaranteed.",
                    "hook": "This supplement cures",
                    "call_to_action": "Buy now",
                },
                "source_clip_id": "clip_123",
                "voice_profile": {"sample_duration": 15.0},
            },
        },
    )

    stage = PreGateStage()
    result = await stage.run(ctx)
    assert result.passed
    gates = result.output["gates"]
    assert gates["claims"] is False


@pytest.mark.asyncio
async def test_pregate_stage_fails_no_source(session: AsyncSession):
    user, persona = await _setup_user(session)

    ctx = StageContext(
        session=session,
        project_id="proj_b",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "script": {
                    "text": "Nice product.",
                    "hook": "Hey everyone",
                    "call_to_action": "Check it out",
                },
                "voice_profile": {"sample_duration": 15.0},
            },
        },
    )

    stage = PreGateStage()
    result = await stage.run(ctx)
    assert not result.passed
    assert not result.output["gates"]["source_quality"]
