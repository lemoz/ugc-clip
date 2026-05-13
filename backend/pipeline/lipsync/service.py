"""Lip sync service — wraps RunComfy API (ported from GOV CLIP)."""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LipsyncResult:
    video_path: str
    duration_seconds: float
    model: str = "lipsync/v2"
    attempt: int = 1


class LipsyncService(abc.ABC):
    @abc.abstractmethod
    async def generate(
        self,
        video_path: str,
        audio_path: str,
        output_dir: str = "/tmp",
    ) -> LipsyncResult:
        ...


class StubLipsyncService(LipsyncService):
    """Stub lip sync service for local development — copies the source video."""

    async def generate(
        self,
        video_path: str,
        audio_path: str,
        output_dir: str = "/tmp",
    ) -> LipsyncResult:
        import shutil
        import uuid
        from pathlib import Path

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"lipsync_{uuid.uuid4().hex[:8]}.mp4"

        if Path(video_path).exists():
            shutil.copy2(video_path, output_path)
        else:
            output_path.write_bytes(b"fake_mp4_content")

        logger.info("Stub lip sync copied video to %s", output_path)

        return LipsyncResult(
            video_path=str(output_path),
            duration_seconds=10.0,
        )
