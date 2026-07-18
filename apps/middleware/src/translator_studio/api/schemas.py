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


class SettingsUpdateRequest(BaseModel):
    llama_server: LlamaServerUpdate | None = None
    detector: DetectorUpdate | None = None
    persist: bool = True
