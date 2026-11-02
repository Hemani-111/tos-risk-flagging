from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.ml.model_loader import model_loader
from app.models.schemas import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Readiness check: report healthy only when the configured model is loadable."""
    try:
        package = model_loader.package_info()
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "version": settings.VERSION},
        )
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        modelVersion=package["modelVersion"],
    )


@router.get("/live")
async def liveness_check():
    return {"status": "ok", "version": settings.VERSION}
