from __future__ import annotations

from pathlib import Path


class TemplateRepository:
    """Loads prompt templates (markdown) from the prompts directory."""

    def __init__(self, prompts_dir: str | Path):
        self._dir = Path(prompts_dir)

    def get(self, name: str) -> str:
        path = self._dir / name
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def system_rules(self) -> str:
        return self.get("system.md")
