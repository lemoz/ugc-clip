"""TTS service — wraps Qwen3-TTS on GCP GPU VMs (ported from GOV CLIP)."""

from __future__ import annotations

import abc
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TtsResult:
    audio_path: str
    duration_seconds: float
    model: str = "qwen3-tts"
    attempt: int = 1


class TtsService(abc.ABC):
    @abc.abstractmethod
    async def generate(
        self,
        script_text: str,
        voice_prompt_audio: str,
        voice_prompt_text: str | None = None,
        output_dir: str = "/tmp",
    ) -> TtsResult:
        ...


class StubTtsService(TtsService):
    """Stub TTS service for local development — creates a dummy WAV file."""

    async def generate(
        self,
        script_text: str,
        voice_prompt_audio: str,
        voice_prompt_text: str | None = None,
        output_dir: str = "/tmp",
    ) -> TtsResult:
        import uuid
        from pathlib import Path

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"tts_{uuid.uuid4().hex[:8]}.wav"

        with open(output_path, "wb") as f:
            f.write(b"RIFF$\x00\x00\x00WAVE")

        duration = len(script_text.split()) / 2.5
        logger.info("Stub TTS generated audio at %s (%.1fs)", output_path, duration)

        return TtsResult(
            audio_path=str(output_path),
            duration_seconds=duration,
        )


class SubprocessTtsService(TtsService):
    """Run a GOV CLIP-compatible TTS script as a subprocess."""

    def __init__(self, script_path: str, python_bin: str = "python3", cwd: str | None = None):
        self.script_path = script_path
        self.python_bin = python_bin
        self.cwd = cwd

    async def generate(
        self,
        script_text: str,
        voice_prompt_audio: str,
        voice_prompt_text: str | None = None,
        output_dir: str = "/tmp",
    ) -> TtsResult:
        import uuid

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        script_file = out_dir / f"script_{uuid.uuid4().hex[:8]}.txt"
        output_path = out_dir / f"tts_{uuid.uuid4().hex[:8]}.wav"
        script_file.write_text(script_text)

        proc = await asyncio.create_subprocess_exec(
            self.python_bin,
            self.script_path,
            "--script",
            str(script_file),
            "--prompt-audio",
            voice_prompt_audio,
            "--output",
            str(output_path),
            cwd=self.cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"TTS subprocess failed ({proc.returncode}): {stderr.decode()[-1000:]}"
            )
        if not output_path.exists():
            raise RuntimeError(f"TTS subprocess did not create output: {output_path}")

        duration = len(script_text.split()) / 2.5
        logger.info("Subprocess TTS generated %s: %s", output_path, stdout.decode()[-300:])
        return TtsResult(audio_path=str(output_path), duration_seconds=duration)


def get_tts_service() -> TtsService:
    from backend.config import load_settings

    settings = load_settings()
    if settings.tts_provider == "subprocess":
        if not settings.govclip_tts_script:
            raise RuntimeError("UGC_GOVCLIP_TTS_SCRIPT is required for subprocess TTS")
        return SubprocessTtsService(
            script_path=settings.govclip_tts_script,
            python_bin=settings.external_python_bin,
            cwd=settings.govclip_root,
        )
    return StubTtsService()
