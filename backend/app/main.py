from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db, engine
from app.api.routes import health_router, audit_runs_router, fixtures_router
from app.services.inspections import register_core_inspections

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    register_core_inspections()
    yield
    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Independent auditing console for AI agents",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health_router)
    app.include_router(audit_runs_router, prefix="/api/v1")
    app.include_router(fixtures_router, prefix="/api/v1")

    return app


# For direct uvicorn run
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)