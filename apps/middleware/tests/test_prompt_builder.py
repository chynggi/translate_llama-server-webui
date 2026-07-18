from translator_studio.detector.service import DetectorService
from translator_studio.prompt.builder import PromptBuilder, format_glossary
from translator_studio.prompt.models import Preset
from translator_studio.prompt.templates import TemplateRepository

from .conftest import make_glossary


def _builder(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir(exist_ok=True)
    (prompts / "system.md").write_text("SYSTEM_RULE_BASE", encoding="utf-8")
    return PromptBuilder(TemplateRepository(prompts))


def _preset():
    return Preset(
        id="bluearchive",
        style="STYLE_RULE",
        user_instruction="TRANSLATE_INSTRUCTION",
        temperature=0.3,
    )


def _detected(source):
    return DetectorService().detect(source, make_glossary())


def test_fixed_prompt_order(tmp_path):
    builder = _builder(tmp_path)
    source = "空崎ヒナがゲヘナに向かった。"
    assembled = builder.build(source, _preset(), _detected(source))
    assert len(assembled.messages) == 2
    system = assembled.messages[0]["content"]
    user = assembled.messages[1]["content"]
    # system: rules -> style -> glossary
    assert system.index("SYSTEM_RULE_BASE") < system.index("STYLE_RULE")
    assert system.index("STYLE_RULE") < system.index("Glossary")
    # user: instruction -> source
    assert user.index("TRANSLATE_INSTRUCTION") < user.index(source)


def test_only_detected_entries_injected(tmp_path):
    builder = _builder(tmp_path)
    source = "空崎ヒナだけ登場。"
    assembled = builder.build(source, _preset(), _detected(source))
    system = assembled.messages[0]["content"]
    assert "空崎ヒナ = 소라사키 히나" in system
    assert "陸八魔アル" not in system  # not in source, must not be injected


def test_no_glossary_block_when_nothing_detected(tmp_path):
    builder = _builder(tmp_path)
    source = "관계없는 문장."
    assembled = builder.build(source, _preset(), _detected(source))
    system = assembled.messages[0]["content"]
    assert "Glossary" not in system


def test_user_instruction_override(tmp_path):
    builder = _builder(tmp_path)
    assembled = builder.build("テスト", _preset(), _detected("テスト"), user_instruction="CUSTOM")
    assert "CUSTOM" in assembled.messages[-1]["content"]
    assert "TRANSLATE_INSTRUCTION" not in assembled.messages[-1]["content"]


def test_preset_params_propagated(tmp_path):
    builder = _builder(tmp_path)
    assembled = builder.build("テスト", _preset(), _detected("テスト"))
    assert assembled.params["temperature"] == 0.3


def test_format_glossary_groups_by_category():
    detected = DetectorService().detect("空崎ヒナがゲヘナへ", make_glossary())
    block = format_glossary(detected)
    assert block.startswith("Glossary")
    assert "[students]" in block
    assert "[locations]" in block
    assert "空崎ヒナ = 소라사키 히나" in block
    assert "ゲヘナ = 게헨나" in block
