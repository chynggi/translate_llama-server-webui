from __future__ import annotations

from fastapi import APIRouter, Depends

from ..container import Services
from .deps import get_services

router = APIRouter()


@router.get("/logs")
async def get_logs(
    limit: int = 50, offset: int = 0, services: Services = Depends(get_services)
):
    return services.logger.list(limit, offset)
