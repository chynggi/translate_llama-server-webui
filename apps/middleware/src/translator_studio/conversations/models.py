"""Conversation data model matching the llama.app / llama.cpp webui JSONL
export format:

    {"type":"session","harness":"llama.app","id":...,"name":...,"lastModified":...,"currNode":...,"thinkingEnabled":...}
    {"type":"message","message":{"id":...,"convId":...,"type":"root","role":"system","content":"",...}}
    {"type":"message","message":{"id":...,"convId":...,"type":"text","role":"user","content":"...",...,"parent":...,"children":[...]}}

Messages form a tree via ``parent``/``children``; ``session.currNode`` points
at the active leaf, which gives branching (sibling regeneration, edit-fork)
semantics identical to the llama webui.
"""

from __future__ import annotations

import time
import uuid

from pydantic import BaseModel, ConfigDict, Field

HARNESS = "llama.app"

# Message types observed in llama.app exports.
TYPE_ROOT = "root"
TYPE_TEXT = "text"
TYPE_SYSTEM = "system"

ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"


def new_id() -> str:
    return str(uuid.uuid4())


def now_ms() -> int:
    return int(time.time() * 1000)


class MessageTimings(BaseModel):
    """Token/timing stats streamed by llama-server (llama.cpp `timings` object).

    Unknown keys (e.g. speculative-decoding stats) are preserved verbatim so
    exports stay loss-free.
    """

    model_config = ConfigDict(extra="allow")

    cache_n: int | None = None
    prompt_n: int | None = None
    prompt_ms: float | None = None
    prompt_per_token_ms: float | None = None
    prompt_per_second: float | None = None
    predicted_n: int | None = None
    predicted_ms: float | None = None
    predicted_per_token_ms: float | None = None
    predicted_per_second: float | None = None
    draft_n: int | None = None
    draft_n_accepted: int | None = None


class MessageExtra(BaseModel):
    """Attachment/metadata entry. ``type`` is open-ended (TEXT, image_file,
    TRANSLATION_META, ...); remaining keys are kept verbatim."""

    model_config = ConfigDict(extra="allow")

    type: str


class ConversationMessage(BaseModel):
    """One node in the conversation tree. Fields not explicitly modelled
    (toolCalls, toolCallId, thinking, ...) are preserved verbatim."""

    model_config = ConfigDict(extra="allow")

    id: str
    convId: str
    type: str = TYPE_TEXT
    timestamp: int = Field(default_factory=now_ms)
    role: str = ROLE_USER
    content: str = ""
    parent: str | None = None
    children: list[str] = Field(default_factory=list)
    extra: list[MessageExtra] | None = None
    model: str | None = None
    completionId: str | None = None
    reasoningContent: str | None = None
    timings: MessageTimings | None = None

    def to_jsonl_line(self) -> dict:
        # exclude_unset preserves only keys that were present on import
        # (including explicit nulls), so round-trips are loss-free; newly
        # created messages still carry the essential fields via setdefault.
        data = self.model_dump(exclude_unset=True, exclude_none=False)
        for key in (
            "id",
            "convId",
            "type",
            "timestamp",
            "role",
            "content",
            "parent",
            "children",
        ):
            data.setdefault(key, getattr(self, key))
        # llama.app exports always carry ``parent`` (null on the root message).
        data["parent"] = self.parent
        return {"type": "message", "message": data}


class ConversationSession(BaseModel):
    """Session header. Fields not explicitly modelled (mcpServerOverrides,
    pinned, folderId, tags, archived, ...) are preserved verbatim."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str = ""
    lastModified: int = Field(default_factory=now_ms)
    currNode: str | None = None
    thinkingEnabled: bool = False
    harness: str = HARNESS
    reasoningEffort: str | None = None
    forkedFromConversationId: str | None = None

    def to_jsonl_line(self) -> dict:
        # exclude_unset preserves only keys present on import (incl. nulls),
        # so round-trips stay loss-free; essential fields are always carried.
        data = self.model_dump(exclude_unset=True, exclude_none=False)
        for key in ("id", "name", "lastModified", "currNode", "thinkingEnabled", "harness"):
            data.setdefault(key, getattr(self, key))
        return {"type": "session", **data}
