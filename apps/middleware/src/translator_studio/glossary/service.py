from __future__ import annotations

from pathlib import Path

from .models import Glossary, GlossaryEntry
from .repository import GlossaryRepository


class GlossaryService:
    """High-level glossary operations shared by the detector and the API."""

    def __init__(self, repository: GlossaryRepository):
        self._repo = repository

    @classmethod
    def from_dir(cls, directory: str | Path) -> "GlossaryService":
        return cls(GlossaryRepository(directory))

    def get_glossary(self, category_names: list[str] | None = None) -> Glossary:
        return self._repo.get_glossary().filtered(category_names)

    def search(self, query: str | None = None, category: str | None = None) -> Glossary:
        return self._repo.search(query, category)

    def upsert(
        self, category: str, source: str, ko: str, aliases: list[str] | None = None
    ) -> GlossaryEntry:
        entry = GlossaryEntry(source=source, ko=ko, aliases=aliases or [])
        return self._repo.upsert(category, entry)

    def import_yaml(self, text: str) -> dict[str, int]:
        return self._repo.import_yaml(text)

    def export_yaml(self, category: str | None = None) -> str:
        return self._repo.export_yaml(category)

    def reload(self) -> None:
        self._repo.reload()
