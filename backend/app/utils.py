from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    """UTC timestamp like ``2026-10-29T10:00:00.000Z`` (matches what the frontend emits)."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
