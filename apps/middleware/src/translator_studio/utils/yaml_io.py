from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


def _safe() -> YAML:
    return YAML(typ="safe", pure=True)


def read_yaml(path: str | Path) -> Any:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return _safe().load(f)


def read_yaml_text(text: str) -> Any:
    return _safe().load(text)
