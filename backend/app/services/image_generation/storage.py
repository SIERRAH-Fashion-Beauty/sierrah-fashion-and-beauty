from __future__ import annotations

import uuid
from pathlib import Path

EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class MediaStore:
    """Stores generated images on disk under ``<media_dir>/generated``.

    File names are random (never derived from user input) so there is no path-traversal
    surface, and a regenerated image gets a new name so browsers never show a stale one.
    """

    def __init__(self, media_dir: Path) -> None:
        self.root = media_dir
        self.generated = media_dir / "generated"
        self.generated.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, mime: str) -> str:
        name = f"{uuid.uuid4().hex}.{EXTENSIONS.get(mime, 'jpg')}"
        (self.generated / name).write_bytes(data)
        return name

    def exists(self, file_name: str) -> bool:
        return self._path(file_name) is not None

    def delete(self, file_name: str) -> None:
        path = self._path(file_name)
        if path:
            path.unlink(missing_ok=True)

    def _path(self, file_name: str) -> Path | None:
        candidate = (self.generated / file_name).resolve()
        if self.generated.resolve() not in candidate.parents or not candidate.is_file():
            return None
        return candidate
