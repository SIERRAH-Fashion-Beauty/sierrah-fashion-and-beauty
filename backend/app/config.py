from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

_DEFAULT_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:4173,http://127.0.0.1:4173"
)


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _resolve(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else BACKEND_DIR / path


def _frontend_public() -> Path | None:
    raw = os.getenv("FRONTEND_PUBLIC_DIR", "").strip()
    candidate = _resolve(raw) if raw else BACKEND_DIR.parent / "frontend" / "public"
    return candidate if candidate.is_dir() else None


@dataclass(frozen=True)
class Settings:
    """Runtime configuration, read from environment variables (and backend/.env)."""

    database_path: Path = field(
        default_factory=lambda: _resolve(os.getenv("DATABASE_PATH", "data/sierrah.db"))
    )
    media_dir: Path = field(
        default_factory=lambda: _resolve(os.getenv("MEDIA_DIR", "data/media"))
    )
    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",")
            if o.strip()
        ]
    )
    seed_demo_data: bool = field(
        default_factory=lambda: _bool(os.getenv("SEED_DEMO_DATA"), True)
    )
    # Folder holding the frontend's static images; lets the backend send demo
    # wardrobe photos to the image provider as optional references.
    frontend_public_dir: Path | None = field(default_factory=_frontend_public)

    # --- Image generation (keys stay on the server) -------------------------
    image_provider: str = field(
        default_factory=lambda: os.getenv("IMAGE_PROVIDER", "none").strip().lower()
    )
    image_api_key: str = field(default_factory=lambda: os.getenv("IMAGE_API_KEY", "").strip())
    image_model: str = field(default_factory=lambda: os.getenv("IMAGE_MODEL", "").strip())
    image_api_base_url: str = field(
        default_factory=lambda: os.getenv("IMAGE_API_BASE_URL", "").strip().rstrip("/")
    )
    image_size: str = field(default_factory=lambda: os.getenv("IMAGE_SIZE", "1024x1536").strip())
    image_quality: str = field(default_factory=lambda: os.getenv("IMAGE_QUALITY", "medium").strip())
    image_timeout_seconds: float = field(default_factory=lambda: _float("IMAGE_TIMEOUT_SECONDS", 150))
    image_max_retries: int = field(default_factory=lambda: _int("IMAGE_MAX_RETRIES", 1))
    image_max_per_hour: int = field(default_factory=lambda: _int("IMAGE_MAX_PER_HOUR", 30))
    image_max_reference_images: int = field(default_factory=lambda: _int("IMAGE_MAX_REFERENCE_IMAGES", 4))
    image_max_reference_bytes: int = field(
        default_factory=lambda: _int("IMAGE_MAX_REFERENCE_BYTES", 4_000_000)
    )


def get_settings() -> Settings:
    return Settings()
