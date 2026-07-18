from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..container import Services
from .deps import get_services

router = APIRouter()


@router.get("/presets")
async def list_presets(services: Services = Depends(get_services)):
    return {"presets": [preset.model_dump() for preset in services.presets.list()]}


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str, services: Services = Depends(get_services)):
    try:
        return services.presets.get(preset_id).model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
