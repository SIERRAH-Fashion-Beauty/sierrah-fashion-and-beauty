"""Optional clothing reference images.

Only photos of garments that are part of the outfit and that the user already stored
in their own wardrobe are used. Everything is validated before it leaves the server:
allowed types by *content* (magic bytes), a hard size cap and a count cap. No face or
person photo is ever requested or sent.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from pathlib import Path

from ...config import Settings
from ...repositories import WardrobeRepository
from ...schemas import Outfit

ALLOWED_SUFFIXES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


@dataclass(frozen=True)
class ReferenceImage:
    data: bytes
    mime: str
    filename: str


def sniff_mime(data: bytes) -> str | None:
    """Identify an image by its first bytes rather than trusting a header or extension."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def decode_data_url(value: str, max_bytes: int) -> ReferenceImage | None:
    if not value.startswith("data:image/") or ";base64," not in value:
        return None
    payload = value.split(";base64,", 1)[1]
    if len(payload) > max_bytes * 4 // 3 + 8:
        return None
    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        return None
    mime = sniff_mime(data)
    if not mime or len(data) > max_bytes:
        return None
    return ReferenceImage(data=data, mime=mime, filename=f"reference.{mime.split('/')[1]}")


def read_public_file(value: str, public_dir: Path | None, max_bytes: int) -> ReferenceImage | None:
    """Read a ``/images/...`` file from the frontend's public folder, refusing path tricks."""
    if public_dir is None or not value.startswith("/") or value.startswith("//"):
        return None
    root = public_dir.resolve()
    target = (root / value.lstrip("/")).resolve()
    if root not in target.parents or target.suffix.lower() not in ALLOWED_SUFFIXES or not target.is_file():
        return None
    if target.stat().st_size > max_bytes:
        return None
    data = target.read_bytes()
    mime = sniff_mime(data)
    return ReferenceImage(data=data, mime=mime, filename=target.name) if mime else None


def collect_references(outfit: Outfit, wardrobe: WardrobeRepository, settings: Settings) -> list[ReferenceImage]:
    """Gather up to ``IMAGE_MAX_REFERENCE_IMAGES`` validated photos of the outfit's owned garments."""
    found: list[ReferenceImage] = []
    seen: set[str] = set()
    for item in outfit.items:
        if item.slot not in ("outfit", "footwear", "bag", "jewellery"):
            continue
        for piece in item.pieces:
            if piece.source != "wardrobe" or not piece.wardrobe_item_id or piece.wardrobe_item_id in seen:
                continue
            seen.add(piece.wardrobe_item_id)
            stored = wardrobe.get(piece.wardrobe_item_id)
            if stored is None or not stored.image:
                continue
            ref = decode_data_url(stored.image, settings.image_max_reference_bytes) or read_public_file(
                stored.image, settings.frontend_public_dir, settings.image_max_reference_bytes
            )
            if ref:
                found.append(ref)
            if len(found) >= settings.image_max_reference_images:
                return found
    return found
