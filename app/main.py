from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.config.tracing import configure_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_tracing(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
