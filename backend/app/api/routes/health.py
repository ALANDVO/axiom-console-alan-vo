from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    # Check database connectivity
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        database=db_status,
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check for Kubernetes."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503