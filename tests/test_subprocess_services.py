from __future__ import annotations

from pathlib import Path

import pytest

from backend.pipeline.lipsync.service import SubprocessLipsyncService
from backend.pipeline.tts.service import SubprocessTtsService


@pytest.mark.asyncio
async def test_subprocess_tts_service(tmp_path: Path):
    script = tmp_path / "fake_tts.py"
    script.write_text(
        """
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--script')
parser.add_argument('--prompt-audio')
parser.add_argument('--output')
args = parser.parse_args()
open(args.output, 'wb').write(b'RIFF$\\x00\\x00\\x00WAVE')
""".strip()
    )
    prompt = tmp_path / "prompt.wav"
    prompt.write_bytes(b"RIFF")

    service = SubprocessTtsService(str(script))
    result = await service.generate(
        "hello world from subprocess", str(prompt), output_dir=str(tmp_path)
    )

    assert Path(result.audio_path).exists()
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_subprocess_lipsync_service(tmp_path: Path):
    script = tmp_path / "fake_lipsync.py"
    script.write_text(
        """
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--audio')
parser.add_argument('--video')
parser.add_argument('--output')
args = parser.parse_args()
open(args.output, 'wb').write(b'fake lipsync video')
""".strip()
    )
    audio = tmp_path / "audio.wav"
    video = tmp_path / "video.mp4"
    audio.write_bytes(b"RIFF")
    video.write_bytes(b"video")

    service = SubprocessLipsyncService(str(script))
    result = await service.generate(str(video), str(audio), output_dir=str(tmp_path))

    assert Path(result.video_path).exists()
    assert Path(result.video_path).read_bytes() == b"fake lipsync video"
