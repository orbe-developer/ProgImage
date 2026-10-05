"""FastAPI application entry point.

Replaces the deprecated ``@app.on_event('startup')`` / ``on_event('shutdown')``
pattern with an ``asynccontextmanager`` lifespan. On startup the lifespan
ensures ORM tables exist (dev convenience; production should rely on
Alembic migrations) and on shutdown it disposes the async engine cleanly.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app import models  # noqa: F401 — registers User, Image on Base.metadata
from app.auth.router import router as auth_router
from app.config import settings
from app.database import Base, engine
from app.routers.image_filtering import router as image_filtering_router
from app.routers.image_masking import router as image_masking_router
from app.routers.image_processing import router as image_processing_router
from app.routers.images import router as images_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create tables at startup, dispose engine at shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "Image storage, retrieval, and transformation API with JWT "
        "authentication and per-owner access control."
    ),
    lifespan=lifespan,
)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1.include_router(images_router, tags=["images"])
api_v1.include_router(image_processing_router, prefix="/images", tags=["image-processing"])
api_v1.include_router(image_filtering_router, prefix="/images", tags=["image-filtering"])
api_v1.include_router(image_masking_router, prefix="/images", tags=["image-masking"])

app.include_router(api_v1)
