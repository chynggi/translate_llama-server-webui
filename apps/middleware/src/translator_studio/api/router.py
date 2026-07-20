from __future__ import annotations

from fastapi import APIRouter

from . import (
    conversations,
    glossary,
    logs,
    openai_proxy,
    presets,
    preview,
    settings,
    translate,
)


def build_router() -> APIRouter:
    router = APIRouter()
    router.include_router(openai_proxy.router)
    router.include_router(translate.router)
    router.include_router(preview.router)
    router.include_router(presets.router)
    router.include_router(glossary.router)
    router.include_router(logs.router)
    router.include_router(settings.router)
    router.include_router(conversations.router)
    return router
