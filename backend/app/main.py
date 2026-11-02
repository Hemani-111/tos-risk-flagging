from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, analysis
from app.core.config import settings
from app.ml.model_loader import model_loader
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        model_loader.load()
    except Exception as exc:
        logger.error("Model package is not ready: %s", exc)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Terms of Service risk analysis API.",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS_STR.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(analysis.router, prefix=settings.API_V1_STR, tags=["analysis"])


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "modelVersion": model_loader.metadata.get("model_version") if model_loader.metadata else None,
    }
