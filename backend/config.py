"""Configuration from environment variables using pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8000
    secret_key: str = "change-me"
    auto_create_tables: bool = True
    database_url: str = "sqlite+aiosqlite:///data/ugc_clip.db"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    gcp_project_id: str | None = None
    gcp_zone: str = "us-central1-a"
    gcp_machine_type: str = "g2-standard-4"
    gcp_gpu_type: str = "nvidia-l4"
    gcp_gpu_count: int = 1
    gcp_image_project: str = "deeplearning-platform-release"
    gcp_image: str = "pytorch-2-7-cu128-ubuntu-2204-nvidia-570-v20260129"
    qwen_model_id: str = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
    qwen_dtype: str = "float32"
    qwen_attn_implementation: str = ""
    qwen_language: str = "English"

    runcomfy_api_token: str | None = None
    runcomfy_base_url: str = "https://model-api.runcomfy.net/v1"

    gcs_bucket: str = "ugc-clip-temp-files"
    s3_bucket: str = "ugc-clip-uploads"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    persona_api_key: str | None = None
    persona_template_id: str | None = None
    persona_webhook_secret: str | None = None

    fal_ai_key: str | None = None
    fal_ai_base_url: str = "https://queue.fal.run"
    fal_ai_image_model: str = "fal-ai/flux/schnell"

    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_pro: str | None = None
    stripe_price_agency: str | None = None

    max_tts_concurrent: int = 1
    max_lipsync_concurrent: int = 3
    max_other_jobs_concurrent: int = 5
    cost_cap_per_project_usd: float = 3.0
    min_voice_sample_duration: int = 15
    max_segment_duration: int = 15
    max_project_retries: int = 3

    templates_dir: str = "templates"
    data_dir: str = "data"
    local_asset_dir: str = "local_assets"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="UGC_",
    )


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()


def resolve_path(relative: str) -> Path:
    path = Path(relative).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path
