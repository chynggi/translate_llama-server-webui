from __future__ import annotations

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    source: str
    preset: str
    glossary_set: list[str] | None = None
    user_instruction: str | None = None
    model: str | None = None
    stream: bool = False
    params: dict = Field(default_factory=dict)


class PreviewRequest(BaseModel):
    source: str
    preset: str
    glossary_set: list[str] | None = None
    user_instruction: str | None = None
    model: str | None = None


class GlossaryPostRequest(BaseModel):
    action: str  # "upsert" | "import"
    category: str | None = None
    source: str | None = None
    ko: str | None = None
    aliases: list[str] | None = None
    yaml: str | None = None


class LlamaServerUpdate(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    default_model: str | None = None
    request_timeout: float | None = None


class DetectorUpdate(BaseModel):
    min_alias_length: int | None = None
    longest_match_first: bool | None = None


class GenerationUpdate(BaseModel):
    """Partial update for llama.cpp sampling defaults. Only keys explicitly
    present in the request are applied; an explicit null clears the value."""

    temperature: float | None = None
    dynatemp_range: float | None = None
    dynatemp_exponent: float | None = None
    top_k: int | None = None
    top_p: float | None = None
    min_p: float | None = None
    xtc_probability: float | None = None
    xtc_threshold: float | None = None
    max_tokens: int | None = None
    samplers: str | None = None
    repeat_last_n: int | None = None
    repeat_penalty: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    dry_multiplier: float | None = None
    dry_base: float | None = None
    dry_allowed_length: int | None = None
    dry_penalty_last_n: int | None = None


class ChatUpdate(BaseModel):
    enable_thinking: bool | None = None
    exclude_reasoning_from_context: bool | None = None
    system_prompt_file: str | None = None


class SettingsUpdateRequest(BaseModel):
    llama_server: LlamaServerUpdate | None = None
    detector: DetectorUpdate | None = None
    generation: GenerationUpdate | None = None
    chat: ChatUpdate | None = None
    persist: bool = True
