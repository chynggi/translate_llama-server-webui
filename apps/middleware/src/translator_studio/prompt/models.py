from __future__ import annotations

from pydantic import BaseModel, Field


class Preset(BaseModel):
    id: str
    name: str = ""
    description: str = ""
    system_rules: str = ""
    style: str = ""
    user_instruction: str = ""
    model: str = ""
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    params: dict = Field(default_factory=dict)


class PromptParts(BaseModel):
    system_rules: str = ""
    preset: str = ""
    glossary: str = ""
    user_instruction: str = ""
    source: str = ""


class AssembledPrompt(BaseModel):
    messages: list[dict]
    parts: PromptParts
    detected: dict
    model: str = ""
    params: dict = Field(default_factory=dict)

    def full_text(self) -> str:
        return "\n\n".join(str(m.get("content", "")) for m in self.messages)


class PreviewResult(BaseModel):
    messages: list[dict]
    parts: PromptParts
    detected: dict
    token_count: int
    model: str = ""
    preset: str = ""
