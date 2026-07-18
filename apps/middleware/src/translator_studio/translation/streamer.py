from __future__ import annotations

import json

DONE = "[DONE]"


def parse_sse_data(line: str) -> str | None:
    line = line.strip()
    if not line.startswith("data:"):
        return None
    return line[len("data:") :].strip()


def is_done(data: str) -> bool:
    return data == DONE


def extract_delta(chunk: dict) -> str:
    try:
        choice = (chunk.get("choices") or [{}])[0]
        return (choice.get("delta") or {}).get("content") or ""
    except (AttributeError, IndexError, KeyError):
        return ""


def encode_sse(data: dict, event: str | None = None) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    if event:
        return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")
    return f"data: {payload}\n\n".encode("utf-8")
