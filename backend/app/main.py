from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import get_settings
from .database import init_db
from .dependencies import get_engine, get_image_service
from .routers import catalog, outfits, recommendations, saved_looks, wardrobe
from .schemas import HealthResponse
from .seed import seed_sample_looks
from .services.image_generation import ImageError, ImageGenerationService
from .services.image_generation.storage import MediaStore

log = logging.getLogger("sierrah")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    seed_sample_looks(get_engine())
    yield


app = FastAPI(
    title="SIERRAH Fashion & Beauty API",
    description="Wardrobe, occasion-based outfit recommendations, saved looks and AI model previews.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(ImageError)
async def image_error_handler(_: Request, exc: ImageError) -> JSONResponse:
    log.warning("image generation failed: %s (%s)", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "internal_error", "message": "Something went wrong on the server.", "retryable": True}},
    )


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health(images: ImageGenerationService = Depends(get_image_service)) -> HealthResponse:
    return HealthResponse(version=__version__, image_generation=images.status())


# Generated model images are served from here. File names are random UUIDs.
MediaStore(settings.media_dir)  # makes sure the folder exists before mounting
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

app.include_router(wardrobe.router)
app.include_router(recommendations.router)
app.include_router(saved_looks.router)
app.include_router(outfits.router)
app.include_router(catalog.router)
