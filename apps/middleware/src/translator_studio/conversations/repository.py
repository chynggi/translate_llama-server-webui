"""JSONL file store for conversations — one ``{id}.jsonl`` file per
conversation, serialized exactly in the llama.app export format so import and
export are loss-free round-trips."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import (
    ConversationMessage,
    ConversationSession,
    new_id,
    now_ms,
)

_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class ConversationNotFoundError(KeyError):
    pass


class ConversationRepository:
    def __init__(self, conversations_dir: str | Path):
        self._dir = Path(conversations_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ paths
    def _path(self, conv_id: str) -> Path:
        if not _ID_RE.match(conv_id):
            raise ConversationNotFoundError(conv_id)
        return self._dir / f"{conv_id}.jsonl"

    # ------------------------------------------------------------------ read
    def exists(self, conv_id: str) -> bool:
        try:
            return self._path(conv_id).exists()
        except ConversationNotFoundError:
            return False

    def list(self) -> list[ConversationSession]:
        sessions: list[ConversationSession] = []
        for path in sorted(self._dir.glob("*.jsonl")):
            try:
                session, _ = self._read(path)
            except (ValueError, json.JSONDecodeError):
                continue  # skip foreign/corrupt files
            sessions.append(session)
        sessions.sort(key=lambda s: s.lastModified, reverse=True)
        return sessions

    def load(self, conv_id: str) -> tuple[ConversationSession, list[ConversationMessage]]:
        path = self._path(conv_id)
        if not path.exists():
            raise ConversationNotFoundError(conv_id)
        return self._read(path)

    def _read(self, path: Path) -> tuple[ConversationSession, list[ConversationMessage]]:
        session: ConversationSession | None = None
        messages: list[ConversationMessage] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rtype = record.get("type")
            if rtype == "session":
                session = ConversationSession(
                    **{k: v for k, v in record.items() if k != "type"}
                )
            elif rtype == "message":
                messages.append(ConversationMessage(**record["message"]))
        if session is None:
            raise ValueError(f"no session record in {path.name}")
        return session, messages

    # ----------------------------------------------------------------- write
    def save(
        self, session: ConversationSession, messages: list[ConversationMessage]
    ) -> None:
        path = self._path(session.id)
        lines = [session.to_jsonl_line()] + [m.to_jsonl_line() for m in messages]
        text = "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines)
        tmp = path.with_suffix(".jsonl.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)  # atomic on POSIX

    def create(
        self,
        name: str = "",
        thinking_enabled: bool = False,
        system_prompt: str = "",
    ) -> tuple[ConversationSession, list[ConversationMessage]]:
        conv_id = new_id()
        root = ConversationMessage(
            id=new_id(),
            convId=conv_id,
            type="root",
            role="system",
            content=system_prompt,
            parent=None,
        )
        session = ConversationSession(
            id=conv_id,
            name=name,
            currNode=root.id,
            thinkingEnabled=thinking_enabled,
        )
        self.save(session, [root])
        return session, [root]

    def delete(self, conv_id: str) -> None:
        path = self._path(conv_id)
        if not path.exists():
            raise ConversationNotFoundError(conv_id)
        path.unlink()

    # ------------------------------------------------------------ import/export
    def import_jsonl(self, text: str) -> tuple[ConversationSession, list[ConversationMessage]]:
        """Parse a llama.app JSONL export and store it (overwrites same id)."""
        session: ConversationSession | None = None
        messages: list[ConversationMessage] = []
        for raw in text.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            rtype = record.get("type")
            if rtype == "session":
                session = ConversationSession(
                    **{
                        k: v
                        for k, v in record.items()
                        if k != "type" and (k != "id" or v)
                    }
                )
                if session.id is None or session.id == "":
                    session.id = new_id()
            elif rtype == "message":
                messages.append(ConversationMessage(**record["message"]))
        if session is None:
            raise ValueError("no session record in import payload")
        if not messages:
            raise ValueError("no messages in import payload")
        self.save(session, messages)
        return session, messages

    def export_jsonl(self, conv_id: str) -> str:
        session, messages = self.load(conv_id)
        lines = [session.to_jsonl_line()] + [m.to_jsonl_line() for m in messages]
        return "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines)
