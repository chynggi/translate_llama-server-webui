from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ..container import Services
from .deps import get_services

router = APIRouter()


@router.get("/v1/models")
async def list_models(services: Services = Depends(get_services)):
    return await services.llama_client.get_models()


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, services: Services = Depends(get_services)):
    body = await request.json()
    preset_id = body.pop("preset", None)
    user_instruction = body.pop("user_instruction", None)
    glossary_set = body.pop("glossary_set", None)
    if preset_id:
        body = services.translation.enrich_chat_payload(
            body, preset_id, user_instruction, glossary_set
        )
    if body.get("stream"):
        return StreamingResponse(
            services.llama_client.chat_completions_stream_bytes(body),
            media_type="text/event-stream",
        )
    return await services.llama_client.chat_completions(body)
