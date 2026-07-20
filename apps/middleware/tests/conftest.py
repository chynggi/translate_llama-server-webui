from __future__ import annotations

import pytest

from translator_studio.config import (
    DetectorSettings,
    LlamaServerSettings,
    PathSettings,
    ServerSettings,
    Settings,
)
from translator_studio.container import build_services
from translator_studio.glossary.models import Glossary, GlossaryCategory, GlossaryEntry

GLOSSARY_YAML = """students:
  空崎ヒナ:
    ko: 소라사키 히나
    aliases:
      - ヒナ
  陸八魔アル:
    ko: 리쿠하치마 아루
    aliases:
      - アル
locations:
  ゲヘナ:
    ko: 게헨나
organizations:
  便利屋68:
    ko: 흥신소68
"""

PRESET_YAML = """id: bluearchive
name: Blue Archive
style: |
  STYLE_RULE
user_instruction: |
  TRANSLATE_INSTRUCTION
temperature: 0.3
max_tokens: 128
"""

SYSTEM_MD = "SYSTEM_RULE_BASE"


class FakeLlamaClient:
    """Duck-typed stand-in for LlamaClient (no llama-server needed in tests)."""

    def __init__(self):
        self.last_payload = None
        self.stream_lines = [
            'data: {"choices": [{"delta": {"content": "히나: "}}]}',
            'data: {"choices": [{"delta": {"content": "아루, 가자."}}]}',
            "data: [DONE]",
        ]

    async def aclose(self) -> None:
        return None

    async def reconfigure(self, base_url=None, api_key=None, timeout=None) -> None:
        self.reconfigured = {
            "base_url": base_url,
            "api_key": api_key,
            "timeout": timeout,
        }

    async def get_models(self) -> dict:
        return {"object": "list", "data": [{"id": "fake-model", "object": "model"}]}

    async def count_tokens(self, text: str) -> int:
        return len(text)

    async def chat_completions(self, payload: dict) -> dict:
        self.last_payload = payload
        return {
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": "히나: 아루, 가자."}}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    async def chat_completions_stream_lines(self, payload: dict):
        self.last_payload = payload
        for line in self.stream_lines:
            yield line

    async def chat_completions_stream_bytes(self, payload: dict):
        self.last_payload = payload
        for line in self.stream_lines:
            yield (line + "\n\n").encode("utf-8")


def make_glossary() -> Glossary:
    return Glossary(
        categories=[
            GlossaryCategory(
                name="students",
                entries=[
                    GlossaryEntry(source="空崎ヒナ", ko="소라사키 히나", aliases=["ヒナ"]),
                    GlossaryEntry(source="陸八魔アル", ko="리쿠하치마 아루", aliases=["アル"]),
                ],
            ),
            GlossaryCategory(
                name="locations",
                entries=[GlossaryEntry(source="ゲヘナ", ko="게헨나")],
            ),
        ]
    )


@pytest.fixture
def settings(tmp_path) -> Settings:
    glossary_dir = tmp_path / "glossary"
    glossary_dir.mkdir()
    (glossary_dir / "bluearchive.yaml").write_text(GLOSSARY_YAML, encoding="utf-8")
    presets_dir = tmp_path / "presets"
    presets_dir.mkdir()
    (presets_dir / "bluearchive.yaml").write_text(PRESET_YAML, encoding="utf-8")
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "system.md").write_text(SYSTEM_MD, encoding="utf-8")
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    conversations_dir = tmp_path / "conversations"
    conversations_dir.mkdir()
    return Settings(
        llama_server=LlamaServerSettings(
            base_url="http://testserver", default_model="fake-model"
        ),
        paths=PathSettings(
            glossary_dir=glossary_dir,
            presets_dir=presets_dir,
            prompts_dir=prompts_dir,
            logs_dir=logs_dir,
            cache_dir=cache_dir,
            conversations_dir=conversations_dir,
        ),
        server=ServerSettings(),
        detector=DetectorSettings(),
    )


@pytest.fixture
def fake_llama() -> FakeLlamaClient:
    return FakeLlamaClient()


@pytest.fixture
def services(settings, fake_llama, tmp_path):
    return build_services(
        settings,
        llama_client=fake_llama,
        config_path=tmp_path / "config.yaml",
    )
