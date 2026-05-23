from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.db import router as db_router
from app.api.routes.health import router as health_router
from app.api.routes.meta import router as meta_router
from app.core.config import get_settings


def setup_cors(application: FastAPI, origins: list[str]) -> FastAPI:
    """Configure application CORS.
    Args:
        application (FastAPI): FastAPI application instance.
        origins (list[str]): Allowed CORS origins."""
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    return application


def create_app() -> FastAPI:
    """Create FastAPI application.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()]
    application = FastAPI(title=settings.app_name)
    application = setup_cors(application, cors_origins)
    application.include_router(health_router)
    application.include_router(db_router)
    application.include_router(meta_router)
    return application


app = create_app()
