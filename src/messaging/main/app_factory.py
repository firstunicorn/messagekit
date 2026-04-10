"""FastAPI application factory."""

from fastapi import APIRouter, FastAPI

from fastapi_middleware_toolkit import setup_cors_middleware, setup_error_handlers
from messaging.config import settings
from messaging.main.lifespan import lifespan
from messaging.presentation.dlq_routes import router as dlq_router
from messaging.presentation.replay_routes import router as replay_router
from messaging.presentation.router import api_router


def create_app() -> FastAPI:
    """Create the FastAPI app instance."""
    app = FastAPI(
        title=settings.service_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    setup_cors_middleware(
        app,
        settings.allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        max_age=settings.cors_max_age,
    )
    setup_error_handlers(app)
    root_router = APIRouter(prefix=settings.api_prefix)
    root_router.include_router(api_router)
    root_router.include_router(dlq_router)
    root_router.include_router(replay_router)
    app.include_router(root_router)
    return app
