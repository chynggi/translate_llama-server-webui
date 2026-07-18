from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..container import Services
from .deps import get_services
from .schemas import TranslateRequest

router = APIRouter()


@router.post("/translate")
async def translate(req: TranslateRequest, services: Services = Depends(get_services)):
    if req.stream:
        return StreamingResponse(
            services.translation.translate_stream(
                req.source,
                req.preset,
                req.user_instruction,
                req.glossary_set,
                req.model,
                req.params,
            ),
            media_type="text/event-stream",
        )
    try:
        return await services.translation.translate(
            req.source,
            req.preset,
            req.user_instruction,
            req.glossary_set,
            req.model,
            req.params,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
