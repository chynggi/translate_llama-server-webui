from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from ..container import Services
from ..conversations.service import ConversationNotFoundError, ParentNotFoundError
from .deps import get_services

router = APIRouter()


class ConversationCreate(BaseModel):
    name: str = ""
    thinkingEnabled: bool = False


class ConversationPatch(BaseModel):
    name: str | None = None
    currNode: str | None = None
    thinkingEnabled: bool | None = None


class MessageAppend(BaseModel):
    parent: str
    role: str
    content: str = ""
    type: str = "text"
    extra: list[dict] | None = None
    model: str | None = None
    completionId: str | None = None
    reasoningContent: str | None = None
    timings: dict | None = None
    id: str | None = None
    timestamp: int | None = None


class ImportBody(BaseModel):
    jsonl: str = Field(min_length=1)


def _dump_session(session) -> dict:
    return session.model_dump()


def _dump_messages(messages) -> list[dict]:
    return [m.model_dump(exclude_none=True) for m in messages]


@router.get("/conversations")
async def list_conversations(services: Services = Depends(get_services)):
    sessions = services.conversations.list()
    return {"conversations": [_dump_session(s) for s in sessions]}


@router.post("/conversations", status_code=201)
async def create_conversation(
    req: ConversationCreate, services: Services = Depends(get_services)
):
    system_prompt = services.templates.get(services.settings.chat.system_prompt_file)
    session, messages = services.conversations.create(
        name=req.name,
        thinking_enabled=req.thinkingEnabled,
        system_prompt=system_prompt,
    )
    return {"session": _dump_session(session), "messages": _dump_messages(messages)}


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, services: Services = Depends(get_services)):
    try:
        session, messages = services.conversations.get(conv_id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="conversation not found")
    return {"session": _dump_session(session), "messages": _dump_messages(messages)}


@router.patch("/conversations/{conv_id}")
async def patch_conversation(
    conv_id: str, req: ConversationPatch, services: Services = Depends(get_services)
):
    try:
        session = services.conversations.update_session(
            conv_id,
            name=req.name,
            curr_node=req.currNode,
            thinking_enabled=req.thinkingEnabled,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="conversation not found")
    except ParentNotFoundError:
        raise HTTPException(status_code=400, detail="unknown currNode")
    return {"session": _dump_session(session)}


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, services: Services = Depends(get_services)):
    try:
        services.conversations.delete(conv_id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="conversation not found")
    return {"ok": True}


@router.post("/conversations/{conv_id}/messages", status_code=201)
async def append_message(
    conv_id: str, req: MessageAppend, services: Services = Depends(get_services)
):
    try:
        session, message = services.conversations.append_message(
            conv_id,
            parent=req.parent,
            role=req.role,
            content=req.content,
            type=req.type,
            extra=req.extra,
            model=req.model,
            completion_id=req.completionId,
            reasoning_content=req.reasoningContent,
            timings=req.timings,
            message_id=req.id,
            timestamp=req.timestamp,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="conversation not found")
    except ParentNotFoundError:
        raise HTTPException(status_code=400, detail="unknown parent message")
    return {
        "session": _dump_session(session),
        "message": message.model_dump(exclude_none=True),
    }


@router.post("/conversations/import", status_code=201)
async def import_conversation(req: ImportBody, services: Services = Depends(get_services)):
    try:
        session, messages = services.conversations.import_jsonl(req.jsonl)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSONL export: {exc}")
    return {"session": _dump_session(session), "messages": _dump_messages(messages)}


@router.get("/conversations/{conv_id}/export")
async def export_conversation(conv_id: str, services: Services = Depends(get_services)):
    try:
        text = services.conversations.export_jsonl(conv_id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="conversation not found")
    return Response(
        content=text,
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f'attachment; filename="conv_{conv_id}.jsonl"'
        },
    )


@router.get("/chat/system-prompt")
async def chat_system_prompt(services: Services = Depends(get_services)):
    """Default system prompt for plain chat, imported from the llama webui
    settings export (prompts/chat_system.md)."""
    content = services.templates.get(services.settings.chat.system_prompt_file)
    return {"content": content, "file": services.settings.chat.system_prompt_file}
