from __future__ import annotations

import threading
import time
from collections import deque

from ...config import Settings
from ...repositories import ImageRepository, OutfitRepository, SavedLookRepository, WardrobeRepository
from ...schemas import GenerateImageRequest, GenerateImageResponse, ImageStatus
from .errors import LocalRateLimited, OutfitNotFound
from .prompt import build_prompt, build_short_prompt
from .providers import PROVIDERS, ImageProvider, supported_providers
from .references import collect_references
from .storage import MediaStore

DISCLAIMER = (
    "AI-generated visual interpretation of this outfit. It is not an exact try-on of your clothes or a "
    "likeness of you, so colours, cut and details can differ from the real items."
)
SETUP_MESSAGE = (
    "AI model previews are not set up yet. Add IMAGE_PROVIDER=gemini (or openai) and IMAGE_API_KEY to "
    "backend/.env, or use the free keyless IMAGE_PROVIDER=pollinations, then restart the API "
    "(see README, \"AI model images\")."
)


class RateLimiter:
    """Sliding-window limiter that protects the provider bill from runaway clicking."""

    def __init__(self, max_events: int, window_seconds: float = 3600.0) -> None:
        self.max_events = max_events
        self.window = window_seconds
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def check(self) -> None:
        if self.max_events <= 0:
            return
        now = time.monotonic()
        with self._lock:
            while self._events and now - self._events[0] > self.window:
                self._events.popleft()
            if len(self._events) >= self.max_events:
                raise LocalRateLimited(
                    f"Image generation limit reached ({self.max_events} per hour). Please try again later."
                )
            self._events.append(now)


class ImageGenerationService:
    """Coordinates prompt building, the provider call and persistence for one outfit image."""

    def __init__(
        self,
        settings: Settings,
        *,
        outfits: OutfitRepository,
        images: ImageRepository,
        saved: SavedLookRepository,
        wardrobe: WardrobeRepository,
        store: MediaStore,
        provider: ImageProvider | None = None,
    ) -> None:
        self.settings = settings
        self.outfits = outfits
        self.images = images
        self.saved = saved
        self.wardrobe = wardrobe
        self.store = store
        self._provider = provider
        self._limiter = RateLimiter(settings.image_max_per_hour)
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    # ---------------------------------------------------------------- status
    def provider(self) -> ImageProvider | None:
        if self._provider is not None:
            return self._provider
        cls = PROVIDERS.get(self.settings.image_provider)
        if cls is None or (cls.requires_key and not self.settings.image_api_key):
            return None
        self._provider = cls(self.settings)
        return self._provider

    def status(self) -> ImageStatus:
        name = self.settings.image_provider or "none"
        if self._provider is None and name in {"", "none"}:
            return ImageStatus(configured=False, provider="none", message=SETUP_MESSAGE)
        if self._provider is None and name not in PROVIDERS:
            return ImageStatus(
                configured=False,
                provider=name,
                message=f"IMAGE_PROVIDER \"{name}\" is not supported. Supported: {', '.join(supported_providers())}.",
            )
        provider = self.provider()
        if provider is None:
            return ImageStatus(configured=False, provider=name, message="IMAGE_API_KEY is missing. " + SETUP_MESSAGE)
        return ImageStatus(configured=True, provider=provider.name, model=provider.model)

    # -------------------------------------------------------------- generate
    def generate(self, outfit_id: str, request: GenerateImageRequest) -> GenerateImageResponse:
        outfit = self.outfits.get(outfit_id)
        if outfit is None:
            raise OutfitNotFound("This outfit was not found. Create the look again to generate its model preview.")

        status = self.status()
        if not status.configured:
            return GenerateImageResponse(
                status="not_configured", outfit_id=outfit_id, message=status.message, disclaimer=""
            )
        provider = self.provider()
        assert provider is not None

        existing = self.images.get(outfit_id)
        if existing and not request.regenerate and self.store.exists(existing[1]):
            return self._ready(outfit_id, existing[0], cached=True)

        with self._lock_for(outfit_id):
            # Another request may have finished while we waited for the lock.
            existing = self.images.get(outfit_id)
            if existing and not request.regenerate and self.store.exists(existing[1]):
                return self._ready(outfit_id, existing[0], cached=True)

            references = []
            if request.use_reference_images and provider.supports_references:
                references = collect_references(outfit, self.wardrobe, self.settings)
            if getattr(provider, "short_prompt", False):
                prompt = build_short_prompt(outfit, request.appearance)
            else:
                prompt = build_prompt(outfit, request.appearance, with_references=bool(references))

            self._limiter.check()
            result = provider.generate(prompt, references)

            file_name = self.store.save(result.data, result.mime)
            image = self.images.save(
                outfit_id,
                provider=provider.name,
                model=result.model,
                file_name=file_name,
                prompt=prompt,
                used_reference_images=bool(references),
            )
            if existing:
                self.store.delete(existing[1])
            self.outfits.attach_image(outfit_id, image)
            self.saved.attach_image(outfit_id, image)
            message = ""
            if request.use_reference_images and not provider.supports_references:
                message = "This image provider cannot use reference photos, so the image was generated from the outfit description only."
            elif request.use_reference_images and not references:
                message = "No usable clothing photos were found, so the image was generated from the outfit description only."
            return self._ready(outfit_id, image, cached=False, message=message)

    # ----------------------------------------------------------------- utils
    def _ready(self, outfit_id: str, image, *, cached: bool, message: str = "") -> GenerateImageResponse:
        return GenerateImageResponse(
            status="ready", outfit_id=outfit_id, image=image, cached=cached, message=message, disclaimer=DISCLAIMER
        )

    def _lock_for(self, outfit_id: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(outfit_id, threading.Lock())
