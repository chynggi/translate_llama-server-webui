from __future__ import annotations

from pathlib import Path

from ..utils import yaml_io
from .models import Preset


class PresetRepository:
    """Loads translation presets from YAML files (one preset per file)."""

    def __init__(self, presets_dir: str | Path):
        self._dir = Path(presets_dir)
        self._presets = self._load()

    def _load(self) -> dict[str, Preset]:
        presets: dict[str, Preset] = {}
        if not self._dir.exists():
            return presets
        files = sorted(self._dir.glob("*.yaml")) + sorted(self._dir.glob("*.yml"))
        for path in files:
            data = yaml_io.read_yaml(path) or {}
            if not isinstance(data, dict):
                continue
            preset_id = str(data.get("id") or path.stem)
            presets[preset_id] = Preset(**{**data, "id": preset_id})
        return presets

    def reload(self) -> None:
        self._presets = self._load()

    def list(self) -> list[Preset]:
        return list(self._presets.values())

    def get(self, preset_id: str) -> Preset:
        preset = self._presets.get(preset_id)
        if preset is None:
            raise KeyError(f"Unknown preset: {preset_id}")
        return preset
