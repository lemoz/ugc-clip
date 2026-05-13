"""Abstract base class for pipeline stages (0-9)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class StageStatus(IntEnum):
    PENDING = 0
    RUNNING = 1
    PASSED = 2
    FAILED = 3
    SKIPPED = 4


@dataclass
class StageResult:
    stage_number: int
    status: StageStatus
    output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == StageStatus.PASSED

    @classmethod
    def success(cls, stage_number: int, output: dict[str, Any] = None) -> StageResult:
        return cls(stage_number=stage_number, status=StageStatus.PASSED, output=output or {})

    @classmethod
    def failure(
        cls, stage_number: int, errors: list[str], output: dict[str, Any] = None
    ) -> StageResult:
        return cls(
            stage_number=stage_number,
            status=StageStatus.FAILED,
            errors=errors,
            output=output or {},
        )

    @classmethod
    def skipped(cls, stage_number: int, reason: str = "") -> StageResult:
        return cls(
            stage_number=stage_number,
            status=StageStatus.SKIPPED,
            warnings=[reason],
        )


@dataclass
class StageContext:
    session: AsyncSession
    project_id: str
    user_id: str
    persona_id: str
    data: dict[str, Any] = field(default_factory=dict)


class PipelineStage(ABC):
    stage_number: int
    stage_name: str

    @abstractmethod
    async def run(self, ctx: StageContext) -> StageResult:
        ...

    def _log(self, msg: str) -> None:
        from backend.config import load_settings

        settings = load_settings()
        if settings.log_level == "DEBUG":
            print(f"[stage:{self.stage_number}] {msg}")


STAGE_NAMES: dict[int, str] = {
    0: "Onboarding & Verification",
    1: "Content Brief",
    2: "Structured Artifacts",
    3: "Pre-Generation Gates",
    4: "Visual Anchors",
    5: "Segment Generation",
    6: "Audio Mix",
    7: "FFmpeg Assembly",
    8: "Post-Generation Gates",
    9: "Human Review",
}
