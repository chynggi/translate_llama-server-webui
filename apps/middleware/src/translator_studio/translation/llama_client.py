from __future__ import annotations

from typing import Any, AsyncIterator

import httpx


class LlamaClient:
    """Async HTTP client for llama.cpp's llama-server (OpenAI-compatible)."""

    def __init__(self, base_url: str, api_key: str = "", timeout: float = 600.0):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._client = self._make_client()

    def _make_client(self) -> httpx.AsyncClient:
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        return httpx.AsyncClient(
            base_url=self._base_url, headers=headers, timeout=self._timeout
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def reconfigure(
        self, base_url: str | None = None, api_key: str | None = None, timeout: float | None = None
    ) -> None:
        if base_url is not None:
            self._base_url = base_url.rstrip("/")
        if api_key is not None:
            self._api_key = api_key
        if timeout is not None:
            self._timeout = timeout
        await self._client.aclose()
        self._client = self._make_client()

    async def get_models(self) -> dict:
        response = await self._client.get("/v1/models")
        response.raise_for_status()
        return response.json()

    async def count_tokens(self, text: str) -> int:
        response = await self._client.post("/tokenize", json={"content": text})
        response.raise_for_status()
        return len((response.json() or {}).get("tokens", []))

    async def chat_completions(self, payload: dict) -> dict:
        response = await self._client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    async def chat_completions_stream_lines(self, payload: dict) -> AsyncIterator[str]:
        payload = {**payload, "stream": True}
        async with self._client.stream(
            "POST", "/v1/chat/completions", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                yield line

    async def chat_completions_stream_bytes(self, payload: dict) -> AsyncIterator[bytes]:
        payload = {**payload, "stream": True}
        async with self._client.stream(
            "POST", "/v1/chat/completions", json=payload
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk
