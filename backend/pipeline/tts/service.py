"""TTS service — wraps Qwen3-TTS on GCP GPU VMs (ported from GOV CLIP)."""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass

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
