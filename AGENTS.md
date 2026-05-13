# UGC Clip — Development Guide

## Project Architecture

**UGC Clip** is a Python FastAPI monolith that orchestrates a gated pipeline for generating UGC-style videos. Users upload face video + voice samples (or paste URLs), create content briefs from templates, and the pipeline generates segment-based AI videos with identity verification and multi-gate quality control.

```
backend/                    FastAPI application
  main.py                   App factory, CORS, middleware
  config.py                 Pydantic-settings from env
  models/                   SQLAlchemy ORM models
  api/                      Route handlers
  pipeline/                 Generation pipeline
    stages/                 One module per pipeline stage (0-9)
    tts/                    Qwen3-TTS on GCP GPU VMs
    lipsync/                RunComfy lip sync client
    assembler.py            FFmpeg assembly engine
    evaluator.py            Vision LLM quality evaluation
  verification/             Persona/Onfido identity verification
  worker.py                 Async job queue (poll-based)
  templates/                UGC template YAML directory
  templates.py              Template loader + resolver

templates/                  UGC template definitions (YAML)
  product_review.yaml
  testimonial.yaml
  unboxing.yaml
  day_in_life.yaml
  ...

frontend/                   Next.js 14 App Router SPA
```

## Pipeline Stages (0–9)

| Stage | Name | Description |
|-------|------|-------------|
| 0 | Onboard & Verify | Upload video/voice/photo, identity verification, persona creation |
| 1 | Content Brief | User selects UGC template, defines product/CTA/tone → brief.json |
| 2 | Artifacts | LLM generates script.json, style_card.json, shot_plan.json, voice_profile.json |
| 3 | Pre-Gates | Hook check, CTA check, claim safety, source quality, voice quality |
| 4 | Visual Anchors | Extract best frames, generate missing via Fal.ai FLUX |
| 5 | Segments | Per-segment TTS + lip sync, parallel generation |
| 6 | Audio Mix | Voiceover + BGM + SFX, LUFS normalization |
| 7 | Assembly | FFmpeg concat segments, burn captions, watermark, CTA end card |
| 8 | Post-Gates | Vision LLM eval (lip sync, voice match, visual, captions), retry controller |
| 9 | Human Review | User preview + QC report, approve/edit/regenerate, export |

## Development

```bash
# Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run dev server
uvicorn backend.main:app --reload --port 8000

# Run tests
pytest

# Lint
ruff check .
```

## Code Conventions

- **Pydantic models** for all data artifacts and API schemas
- **SQLAlchemy async** for all database access
- **FastAPI dependency injection** for auth, DB sessions, settings
- **No comments** unless required for clarity
- **Type hints** on all public functions
- **Line length**: 100 chars

## API Design

- Routes under `/api/v1/`
- JWT Bearer auth on all authenticated endpoints
- Pydantic models for request/response schemas
- FastAPI background tasks for pipeline stages

## Testing

- pytest + pytest-asyncio for all tests
- Mock external services (OpenRouter, GCP, RunComfy, Persona, Stripe)
- Test each stage independently
- Integration tests for full pipeline

## Key Constraints

- TTS max 1 concurrent job (GCP GPU VMs are expensive)
- Lip sync max 3 concurrent (RunComfy handles parallelism)
- Per-project cost cap: $3.00
- Min voice sample: 15 seconds
- Max segment duration: 15 seconds
- Max regeneration retries: 3
