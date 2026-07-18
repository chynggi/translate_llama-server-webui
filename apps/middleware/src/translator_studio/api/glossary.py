from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from ..container import Services
from ..glossary.models import Glossary
from .deps import get_services
from .schemas import GlossaryPostRequest

router = APIRouter()


def _glossary_response(glossary: Glossary) -> dict:
    data = glossary.model_dump()
    total = sum(len(category["entries"]) for category in data["categories"])
    return {"categories": data["categories"], "total_entries": total}


@router.get("/glossary")
async def get_glossary(
    q: str | None = None,
    category: str | None = None,
    services: Services = Depends(get_services),
):
    return _glossary_response(services.glossary.search(q, category))


@router.get("/glossary/export")
async def export_glossary(
    category: str | None = None, services: Services = Depends(get_services)
):
    yaml_text = services.glossary.export_yaml(category)
    return Response(
        content=yaml_text,
        media_type="application/x-yaml",
        headers={"Content-Disposition": 'attachment; filename="glossary.yaml"'},
    )


@router.post("/glossary")
async def post_glossary(req: GlossaryPostRequest, services: Services = Depends(get_services)):
    if req.action == "import":
        if not req.yaml:
            raise HTTPException(status_code=400, detail="'yaml' is required for import")
        return {"imported": services.glossary.import_yaml(req.yaml)}
    if req.action == "upsert":
        if not req.category or req.source is None or req.ko is None:
            raise HTTPException(
                status_code=400,
                detail="'category', 'source' and 'ko' are required for upsert",
            )
        entry = services.glossary.upsert(req.category, req.source, req.ko, req.aliases or [])
        return entry.model_dump()
    raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")
