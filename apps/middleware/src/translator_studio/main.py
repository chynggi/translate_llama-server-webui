from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api.router import build_router
from .config import Settings, load_settings
from .container import Services, build_services


def create_app(settings: Settings | None = None, services: Services | None = None) -> FastAPI:
    settings = settings or load_settings()
    settings.paths.ensure()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.services = services or build_services(settings)
        yield
        await app.state.services.llama_client.aclose()

    app = FastAPI(title="Translation Studio", version=__version__, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(build_router())

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
