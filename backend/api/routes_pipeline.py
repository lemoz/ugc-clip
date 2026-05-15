"""Pipeline run, status, artifact, review, and download routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.models.base import get_session
from backend.models.project import Project
from backend.models.user import User
from backend.pipeline.artifacts import artifact_content, list_artifacts
from backend.pipeline.defaults import build_default_orchestrator, build_project_context

router = APIRouter(prefix="/api/v1/projects")


class PipelineRunRequest(BaseModel):
    template_slug: str = "product-review"
    start_stage: int = 0
    stop_stage: int = 9


async def _owned_project(session: AsyncSession, user_id: str, project_id: str) -> Project:
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/run")
async def run_pipeline(
    project_id: str,
    body: PipelineRunRequest = PipelineRunRequest(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    project = await _owned_project(session, current_user.id, project_id)
    context = await build_project_context(session, project, template_slug=body.template_slug)
    orchestrator = build_default_orchestrator()
    results = await orchestrator.run(
        session,
        project.id,
        start_stage=body.start_stage,
        stop_stage=body.stop_stage,
        context_data=context,
    )
    await session.refresh(project)
    return {
        "project_id": project.id,
        "status": project.status,
        "stage": project.stage,
        "results": [
            {
                "stage_number": r.stage_number,
                "status": r.status.name.lower(),
                "errors": r.errors,
                "warnings": r.warnings,
                "output": r.output,
            }
            for r in results
        ],
    }


@router.get("/{project_id}/status")
async def project_status(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    project = await _owned_project(session, current_user.id, project_id)
    return {
        "id": project.id,
        "status": project.status,
        "stage": project.stage,
        "error": project.error,
    }


@router.get("/{project_id}/artifacts")
async def project_artifacts(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    project = await _owned_project(session, current_user.id, project_id)
    artifacts = await list_artifacts(session, project.id)
    return [
        {
            "id": a.id,
            "stage_number": a.stage_number,
            "artifact_type": a.artifact_type,
            "status": a.status,
            "content": artifact_content(a),
        }
        for a in artifacts
    ]


@router.post("/{project_id}/approve")
async def approve_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    project = await _owned_project(session, current_user.id, project_id)
    project.status = "approved"
    await session.commit()
    return {"id": project.id, "status": project.status}


@router.get("/{project_id}/download")
async def download_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    project = await _owned_project(session, current_user.id, project_id)
    artifacts = await list_artifacts(session, project.id)
    for artifact in reversed(artifacts):
        content = artifact_content(artifact)
        output = content.get("output", {})
        path = output.get("video_path") or output.get("output_video")
        if path and Path(path).exists():
            return FileResponse(path, media_type="video/mp4", filename=f"{project.id}.mp4")
    raise HTTPException(status_code=404, detail="No generated video found")
