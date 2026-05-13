"""File upload handler — local storage (S3/GCS in production)."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from backend.config import load_settings


async def save_upload(upload: UploadFile, category: str) -> str:
    settings = load_settings()
    data_dir = Path(settings.data_dir)
    category_dir = data_dir / "uploads" / category
    category_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(upload.filename).suffix if upload.filename else ".bin"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = category_dir / filename

    with open(filepath, "wb") as f:
        while chunk := await upload.read(1024 * 1024):
            f.write(chunk)

    return str(filepath.resolve())


def get_upload_path(relative: str) -> Path:
    settings = load_settings()
    data_dir = Path(settings.data_dir)
    return (data_dir / relative).resolve()


def ensure_upload_dir(category: str) -> Path:
    settings = load_settings()
    data_dir = Path(settings.data_dir)
    category_dir = data_dir / "uploads" / category
    category_dir.mkdir(parents=True, exist_ok=True)
    return category_dir
