"""Tree operations over stored conversations: appending messages (which is
also how branches are created — a second child under the same parent), node
activation and session metadata updates."""

from __future__ import annotations

from .models import (
    ConversationMessage,
    ConversationSession,
    MessageTimings,
    new_id,
    now_ms,
)
from .repository import ConversationNotFoundError, ConversationRepository

__all__ = [
    "ConversationService",
    "ConversationNotFoundError",
    "ParentNotFoundError",
    "active_path",
    "siblings_of",
    "descend_to_leaf",
]


class ParentNotFoundError(ValueError):
    pass


# ------------------------------------------------------------- pure helpers
def _index(messages: list[ConversationMessage]) -> dict[str, ConversationMessage]:
    return {m.id: m for m in messages}


def active_path(
    messages: list[ConversationMessage], leaf_id: str | None
) -> list[ConversationMessage]:
    """Walk parents from ``leaf_id`` up to the root; return root-first order."""
    by_id = _index(messages)
    path: list[ConversationMessage] = []
    seen: set[str] = set()
    node = by_id.get(leaf_id or "")
    while node is not None and node.id not in seen:
        seen.add(node.id)
        path.append(node)
        node = by_id.get(node.parent or "")
    path.reverse()
    return path


def siblings_of(
    messages: list[ConversationMessage], node_id: str
) -> list[ConversationMessage]:
    """All messages sharing the same parent (roots share ``parent=None``)."""
    by_id = _index(messages)
    node = by_id.get(node_id)
    if node is None:
        return []
    return [m for m in messages if m.parent == node.parent]


def descend_to_leaf(
    messages: list[ConversationMessage], node_id: str
) -> ConversationMessage | None:
    """Deepest descendant of ``node_id``, preferring the newest child at each
    step (llama webui branch-switch behaviour)."""
    by_id = _index(messages)
    node = by_id.get(node_id)
    if node is None:
        return None
    while node.children:
        candidates = [by_id[c] for c in node.children if c in by_id]
        if not candidates:
            break
        node = max(candidates, key=lambda m: m.timestamp)
    return node


# ----------------------------------------------------------------- service
class ConversationService:
    def __init__(self, repository: ConversationRepository):
        self._repo = repository

    # CRUD ------------------------------------------------------------------
    def list(self) -> list[ConversationSession]:
        return self._repo.list()

    def get(self, conv_id: str) -> tuple[ConversationSession, list[ConversationMessage]]:
        return self._repo.load(conv_id)

    def create(
        self,
        name: str = "",
        thinking_enabled: bool = False,
        system_prompt: str = "",
    ) -> tuple[ConversationSession, list[ConversationMessage]]:
        return self._repo.create(name, thinking_enabled, system_prompt)

    def delete(self, conv_id: str) -> None:
        self._repo.delete(conv_id)

    def import_jsonl(self, text: str):
        return self._repo.import_jsonl(text)

    def export_jsonl(self, conv_id: str) -> str:
        return self._repo.export_jsonl(conv_id)

    # Mutations ---------------------------------------------------------------
    def append_message(
        self,
        conv_id: str,
        *,
        parent: str,
        role: str,
        content: str = "",
        type: str = "text",
        extra: list[dict] | None = None,
        model: str | None = None,
        completion_id: str | None = None,
        reasoning_content: str | None = None,
        timings: dict | None = None,
        message_id: str | None = None,
        timestamp: int | None = None,
    ) -> tuple[ConversationSession, ConversationMessage]:
        session, messages = self._repo.load(conv_id)
        by_id = _index(messages)
        if parent not in by_id:
            raise ParentNotFoundError(parent)
        message = ConversationMessage(
            id=message_id or new_id(),
            convId=conv_id,
            type=type,
            timestamp=timestamp or now_ms(),
            role=role,
            content=content,
            parent=parent,
            extra=extra,
            model=model,
            completionId=completion_id,
            reasoningContent=reasoning_content,
            timings=MessageTimings(**timings) if timings else None,
        )
        by_id[parent].children.append(message.id)
        messages.append(message)
        session.currNode = message.id
        session.lastModified = now_ms()
        self._repo.save(session, messages)
        return session, message

    def update_session(
        self,
        conv_id: str,
        *,
        name: str | None = None,
        curr_node: str | None = None,
        thinking_enabled: bool | None = None,
    ) -> ConversationSession:
        session, messages = self._repo.load(conv_id)
        if name is not None:
            session.name = name
        if curr_node is not None:
            if _index(messages).get(curr_node) is None:
                raise ParentNotFoundError(curr_node)
            session.currNode = curr_node
        if thinking_enabled is not None:
            session.thinkingEnabled = thinking_enabled
        session.lastModified = now_ms()
        self._repo.save(session, messages)
        return session
