"""Lip sync service — wraps RunComfy API (ported from GOV CLIP)."""

from __future__ import annotations

import abc
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

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


class SubprocessLipsyncService(LipsyncService):
    """Run a GOV CLIP-compatible lip sync script as a subprocess."""

    def __init__(self, script_path: str, python_bin: str = "python3", cwd: str | None = None):
        self.script_path = script_path
        self.python_bin = python_bin
        self.cwd = cwd

    async def generate(
        self,
        video_path: str,
        audio_path: str,
        output_dir: str = "/tmp",
    ) -> LipsyncResult:
        import uuid

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"lipsync_{uuid.uuid4().hex[:8]}.mp4"
        proc = await asyncio.create_subprocess_exec(
            self.python_bin,
            self.script_path,
            "--audio",
            audio_path,
            "--video",
            video_path,
            "--output",
            str(output_path),
            cwd=self.cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"Lip sync subprocess failed ({proc.returncode}): {stderr.decode()[-1000:]}"
            )
        if not output_path.exists():
            raise RuntimeError(f"Lip sync subprocess did not create output: {output_path}")

        logger.info("Subprocess lip sync generated %s: %s", output_path, stdout.decode()[-300:])
        return LipsyncResult(video_path=str(output_path), duration_seconds=10.0)


def get_lipsync_service() -> LipsyncService:
    from backend.config import load_settings

    settings = load_settings()
    if settings.lipsync_provider == "subprocess":
        if not settings.govclip_lipsync_script:
            raise RuntimeError("UGC_GOVCLIP_LIPSYNC_SCRIPT is required for subprocess lip sync")
        return SubprocessLipsyncService(
            script_path=settings.govclip_lipsync_script,
            python_bin=settings.external_python_bin,
            cwd=settings.govclip_root,
        )
    return StubLipsyncService()
