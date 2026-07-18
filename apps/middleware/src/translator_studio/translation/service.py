from __future__ import annotations

import json
from typing import Any, AsyncIterator

from pydantic import BaseModel

from ..config import Settings
from ..detector.service import DetectedGlossary, DetectorService
from ..glossary.service import GlossaryService
from ..logs.logger import TranslationLogger
from ..postprocess.service import Postprocessor
from ..prompt.builder import PromptBuilder
from ..prompt.models import AssembledPrompt, Preset, PreviewResult
from ..prompt.presets import PresetRepository
from ..utils.tokens import count_tokens
from . import streamer
from .llama_client import LlamaClient


class TranslateResult(BaseModel):
    id: str
    output: str
    raw_output: str
    detected: dict
    model: str
    preset: str
    tokens: dict


class TranslationService:
    """Orchestrates the translation pipeline:

    load preset -> detect glossary -> build prompt -> call llama.cpp ->
    post-process -> log. llama.cpp stays untouched behind this service.
    """

    def __init__(
        self,
        llama_client: LlamaClient,
        glossary: GlossaryService,
        detector: DetectorService,
        prompt_builder: PromptBuilder,
        presets: PresetRepository,
        postprocessor: Postprocessor,
        logger: TranslationLogger,
        settings: Settings,
    ):
        self._llama = llama_client
        self._glossary = glossary
        self._detector = detector
        self._builder = prompt_builder
        self._presets = presets
        self._post = postprocessor
        self._logger = logger
        self._settings = settings

    def assemble(
        self,
        source: str,
        preset_id: str,
        user_instruction: str | None = None,
        glossary_set: list[str] | None = None,
        model: str | None = None,
    ) -> tuple[Preset, DetectedGlossary, AssembledPrompt]:
        preset = self._presets.get(preset_id)
        glossary = self._glossary.get_glossary(glossary_set)
        detected = self._detector.detect(source, glossary)
        assembled = self._builder.build(source, preset, detected, user_instruction, model)
        return preset, detected, assembled

    def _payload(
        self, assembled: AssembledPrompt, params: dict | None, stream: bool
    ) -> dict:
        payload: dict[str, Any] = {
            "model": assembled.model or self._settings.llama_server.default_model,
            "messages": assembled.messages,
            "stream": stream,
        }
        payload.update(assembled.params)
        if params:
            payload.update(params)
        return payload

    async def translate(
        self,
        source: str,
        preset_id: str,
        user_instruction: str | None = None,
        glossary_set: list[str] | None = None,
        model: str | None = None,
        params: dict | None = None,
    ) -> TranslateResult:
        preset, detected, assembled = self.assemble(
            source, preset_id, user_instruction, glossary_set, model
        )
        payload = self._payload(assembled, params, stream=False)
        response = await self._llama.chat_completions(payload)
        raw = self._extract_content(response)
        output = self._post.process(raw)
        tokens = self._usage(response)
        record = self._logger.log(
            source=source,
            preset=preset.id,
            model=payload["model"],
            detected=detected.to_response(),
            prompt=assembled.messages,
            raw_output=raw,
            output=output,
            tokens=tokens,
        )
        return TranslateResult(
            id=record["id"],
            output=output,
            raw_output=raw,
            detected=detected.to_response(),
            model=payload["model"],
            preset=preset.id,
            tokens=tokens,
        )

    async def translate_stream(
        self,
        source: str,
        preset_id: str,
        user_instruction: str | None = None,
        glossary_set: list[str] | None = None,
        model: str | None = None,
        params: dict | None = None,
    ) -> AsyncIterator[bytes]:
        try:
            preset, detected, assembled = self.assemble(
                source, preset_id, user_instruction, glossary_set, model
            )
        except KeyError as exc:
            yield streamer.encode_sse({"type": "error", "message": str(exc)})
            return
        payload = self._payload(assembled, params, stream=True)
        raw_parts: list[str] = []
        usage: dict = {}
        try:
            async for line in self._llama.chat_completions_stream_lines(payload):
                data = streamer.parse_sse_data(line)
                if data is None:
                    continue
                if streamer.is_done(data):
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if chunk.get("usage"):
                    usage = chunk["usage"]
                delta = streamer.extract_delta(chunk)
                if delta:
                    raw_parts.append(delta)
                    yield streamer.encode_sse({"type": "delta", "content": delta})
            raw = "".join(raw_parts)
            output = self._post.process(raw)
            tokens = usage or await self._estimate_tokens(assembled, raw)
            record = self._logger.log(
                source=source,
                preset=preset.id,
                model=payload["model"],
                detected=detected.to_response(),
                prompt=assembled.messages,
                raw_output=raw,
                output=output,
                tokens=tokens,
            )
            yield streamer.encode_sse(
                {
                    "type": "done",
                    "id": record["id"],
                    "output": output,
                    "raw_output": raw,
                    "detected": detected.to_response(),
                    "messages": assembled.messages,
                    "model": payload["model"],
                    "preset": preset.id,
                    "tokens": tokens,
                },
                event="done",
            )
        except Exception as exc:  # surface upstream errors to the client
            yield streamer.encode_sse({"type": "error", "message": str(exc)})

    async def preview(
        self,
        source: str,
        preset_id: str,
        user_instruction: str | None = None,
        glossary_set: list[str] | None = None,
        model: str | None = None,
    ) -> PreviewResult:
        preset, _, assembled = self.assemble(
            source, preset_id, user_instruction, glossary_set, model
        )
        token_count = await count_tokens(assembled.full_text(), self._llama)
        return PreviewResult(
            messages=assembled.messages,
            parts=assembled.parts,
            detected=assembled.detected,
            token_count=token_count,
            model=assembled.model or self._settings.llama_server.default_model,
            preset=preset.id,
        )

    def enrich_chat_payload(
        self,
        body: dict,
        preset_id: str,
        user_instruction: str | None = None,
        glossary_set: list[str] | None = None,
    ) -> dict:
        messages = body.get("messages", [])
        source = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                source = message.get("content", "")
                break
        _, _, assembled = self.assemble(
            source, preset_id, user_instruction, glossary_set, body.get("model")
        )
        payload = {k: v for k, v in body.items() if k != "messages"}
        payload["messages"] = assembled.messages
        payload.update(assembled.params)
        return payload

    def _extract_content(self, response: dict) -> str:
        try:
            return (response.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        except (IndexError, AttributeError):
            return ""

    def _usage(self, response: dict) -> dict:
        return response.get("usage") or {}

    async def _estimate_tokens(self, assembled: AssembledPrompt, raw: str) -> dict:
        return {
            "prompt_tokens": await count_tokens(assembled.full_text(), self._llama),
            "completion_tokens": await count_tokens(raw, self._llama),
        }
