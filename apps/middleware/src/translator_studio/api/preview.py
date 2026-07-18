from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..container import Services
from .deps import get_services
from .schemas import PreviewRequest

router = APIRouter()


@router.post("/preview")
async def preview(req: PreviewRequest, services: Services = Depends(get_services)):
    try:
        return await services.translation.preview(
            req.source, req.preset, req.user_instruction, req.glossary_set, req.model
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
