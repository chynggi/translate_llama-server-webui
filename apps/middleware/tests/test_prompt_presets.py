import pytest

from translator_studio.prompt.presets import PresetRepository


def test_loads_presets(settings):
    repo = PresetRepository(settings.paths.presets_dir)
    presets = {p.id for p in repo.list()}
    assert "bluearchive" in presets


def test_get_returns_preset_fields(settings):
    repo = PresetRepository(settings.paths.presets_dir)
    preset = repo.get("bluearchive")
    assert preset.name == "Blue Archive"
    assert preset.user_instruction.strip() == "TRANSLATE_INSTRUCTION"
    assert preset.temperature == 0.3
    assert preset.max_tokens == 128


def test_get_unknown_raises(settings):
    repo = PresetRepository(settings.paths.presets_dir)
    with pytest.raises(KeyError):
        repo.get("does-not-exist")
