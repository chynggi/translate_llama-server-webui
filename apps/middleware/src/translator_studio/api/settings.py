from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ..config import DEFAULT_CONFIG_PATH, Settings
from ..container import Services
from .deps import get_services
from .schemas import SettingsUpdateRequest

router = APIRouter()


def _public_settings(settings: Settings) -> dict:
    return {
        "llama_server": {
            "base_url": settings.llama_server.base_url,
            "default_model": settings.llama_server.default_model,
            "request_timeout": settings.llama_server.request_timeout,
            "api_key_set": bool(settings.llama_server.api_key),
        },
        "detector": {
            "min_alias_length": settings.detector.min_alias_length,
            "longest_match_first": settings.detector.longest_match_first,
        },
        "generation": settings.generation.model_dump(),
        "chat": settings.chat.model_dump(),
    }


def _persist_settings(settings: Settings, path: Path = DEFAULT_CONFIG_PATH) -> None:
    yaml = YAML()
    yaml.preserve_quotes = True
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.load(f) or CommentedMap()
    else:
        data = CommentedMap()
        path.parent.mkdir(parents=True, exist_ok=True)

    llama = data.setdefault("llama_server", CommentedMap())
    llama["base_url"] = settings.llama_server.base_url
    llama["api_key"] = settings.llama_server.api_key
    llama["default_model"] = settings.llama_server.default_model
    llama["request_timeout"] = settings.llama_server.request_timeout

    detector = data.setdefault("detector", CommentedMap())
    detector["min_alias_length"] = settings.detector.min_alias_length
    detector["longest_match_first"] = settings.detector.longest_match_first

    generation = data.setdefault("generation", CommentedMap())
    for key, value in settings.generation.model_dump().items():
        if value is None:
            generation.pop(key, None)  # keep the YAML free of cleared values
        else:
            generation[key] = value

    chat = data.setdefault("chat", CommentedMap())
    chat["enable_thinking"] = settings.chat.enable_thinking
    chat["exclude_reasoning_from_context"] = settings.chat.exclude_reasoning_from_context
    chat["system_prompt_file"] = settings.chat.system_prompt_file

    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)


@router.get("/settings")
async def get_settings(services: Services = Depends(get_services)):
    return _public_settings(services.settings)


@router.put("/settings")
async def update_settings(
    req: SettingsUpdateRequest, services: Services = Depends(get_services)
):
    settings = services.settings
    llama_changed = False

    if req.llama_server:
        patch = req.llama_server
        if patch.base_url is not None and patch.base_url != settings.llama_server.base_url:
            settings.llama_server.base_url = patch.base_url
            llama_changed = True
        if patch.api_key is not None and patch.api_key != settings.llama_server.api_key:
            settings.llama_server.api_key = patch.api_key
            llama_changed = True
        if patch.default_model is not None:
            settings.llama_server.default_model = patch.default_model
        if patch.request_timeout is not None:
            settings.llama_server.request_timeout = patch.request_timeout
            llama_changed = True

    if req.detector:
        patch = req.detector
        if patch.min_alias_length is not None:
            settings.detector.min_alias_length = patch.min_alias_length
        if patch.longest_match_first is not None:
            settings.detector.longest_match_first = patch.longest_match_first
        services.detector.configure(
            min_alias_length=settings.detector.min_alias_length,
            longest_match_first=settings.detector.longest_match_first,
        )

    if req.generation:
        # exclude_unset: only explicitly provided keys apply; explicit null clears.
        for key, value in req.generation.model_dump(exclude_unset=True).items():
            setattr(settings.generation, key, value)

    if req.chat:
        for key, value in req.chat.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(settings.chat, key, value)

    if llama_changed:
        await services.llama_client.reconfigure(
            base_url=settings.llama_server.base_url,
            api_key=settings.llama_server.api_key,
            timeout=settings.llama_server.request_timeout,
        )

    if req.persist and services.config_path is not None:
        _persist_settings(settings, services.config_path)

    return _public_settings(settings)
