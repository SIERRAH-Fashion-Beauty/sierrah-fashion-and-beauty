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


@dataclass(frozen=True)
class Settings:
    database_path: Path = field(
        default_factory=lambda: _resolve(os.getenv("DATABASE_PATH", "data/sierrah.db"))
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
    image_provider: str = field(
        default_factory=lambda: os.getenv("IMAGE_PROVIDER", "none").strip().lower()
    )
    image_api_key: str = field(default_factory=lambda: os.getenv("IMAGE_API_KEY", ""))
    image_model: str = field(default_factory=lambda: os.getenv("IMAGE_MODEL", ""))


def _resolve(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else BACKEND_DIR / path


def get_settings() -> Settings:
    return Settings()
