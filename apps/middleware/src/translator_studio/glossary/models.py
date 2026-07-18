from __future__ import annotations

from pydantic import BaseModel, Field


class GlossaryEntry(BaseModel):
    source: str
    ko: str
    aliases: list[str] = Field(default_factory=list)


class GlossaryCategory(BaseModel):
    name: str
    entries: list[GlossaryEntry] = Field(default_factory=list)

    def find(self, source: str) -> GlossaryEntry | None:
        for entry in self.entries:
            if entry.source == source:
                return entry
        return None


class Glossary(BaseModel):
    categories: list[GlossaryCategory] = Field(default_factory=list)

    def category(self, name: str) -> GlossaryCategory | None:
        for category in self.categories:
            if category.name == name:
                return category
        return None

    def category_names(self) -> list[str]:
        return [c.name for c in self.categories]

    def filtered(self, category_names: list[str] | None) -> "Glossary":
        if not category_names:
            return self
        wanted = set(category_names)
        return Glossary(categories=[c for c in self.categories if c.name in wanted])
