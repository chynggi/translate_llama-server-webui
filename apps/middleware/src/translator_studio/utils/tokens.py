from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid circular import at runtime
    from ..translation.llama_client import LlamaClient


def estimate_tokens(text: str) -> int:
    # Fallback when llama-server is unreachable: ~1 token per 2 chars for CJK-heavy text.
    return max(1, (len(text) + 1) // 2)


async def count_tokens(text: str, llama_client: "LlamaClient") -> int:
    if not text:
        return 0
    try:
        return await llama_client.count_tokens(text)
    except Exception:
        return estimate_tokens(text)
