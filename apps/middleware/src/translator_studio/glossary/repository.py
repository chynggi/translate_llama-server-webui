from __future__ import annotations

from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ..utils import yaml_io
from .loader import load_glossary_dir, parse_glossary_data
from .models import Glossary, GlossaryCategory, GlossaryEntry

DEFAULT_FILE = "custom.yaml"


class GlossaryRepository:
    """In-memory glossary with YAML persistence.

    Each category is persisted back to the file it came from (or a default
    file for brand-new categories), so the on-disk multi-file layout the user
    maintains by hand is preserved.
    """

    def __init__(self, glossary_dir: str | Path):
        self._dir = Path(glossary_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._rt = YAML()  # round-trip: keeps comments/formatting on write
        self._rt.preserve_quotes = True
        self.reload()

    def reload(self) -> None:
        self._glossary = load_glossary_dir(self._dir)
        self._category_files = self._map_category_files()

    def _map_category_files(self) -> dict[str, Path]:
        mapping: dict[str, Path] = {}
        files = sorted(self._dir.glob("*.yaml")) + sorted(self._dir.glob("*.yml"))
        for path in files:
            data = yaml_io.read_yaml(path) or {}
            if isinstance(data, dict):
                for category in data.keys():
                    mapping.setdefault(str(category), path)
        return mapping

    def get_glossary(self) -> Glossary:
        return self._glossary

    def search(self, query: str | None = None, category: str | None = None) -> Glossary:
        query = (query or "").strip().lower()
        categories: list[GlossaryCategory] = []
        for cat in self._glossary.categories:
            if category and cat.name != category:
                continue
            entries = cat.entries
            if query:
                entries = [
                    e
                    for e in entries
                    if query in e.source.lower()
                    or query in e.ko.lower()
                    or any(query in a.lower() for a in e.aliases)
                ]
            categories.append(GlossaryCategory(name=cat.name, entries=entries))
        return Glossary(categories=categories)

    def upsert(self, category: str, entry: GlossaryEntry) -> GlossaryEntry:
        cat = self._glossary.category(category)
        if cat is None:
            cat = GlossaryCategory(name=category, entries=[])
            self._glossary.categories.append(cat)
        existing = cat.find(entry.source)
        if existing is None:
            cat.entries.append(entry)
        else:
            existing.ko = entry.ko
            existing.aliases = list(entry.aliases)
        self._persist_category(category)
        return entry

    def import_yaml(self, text: str) -> dict[str, int]:
        parsed = parse_glossary_data(yaml_io.read_yaml_text(text) or {})
        counts: dict[str, int] = {}
        for category, entries in parsed.items():
            for entry in entries.values():
                self.upsert(category, entry)
            counts[category] = len(entries)
        return counts

    def export_yaml(self, category: str | None = None) -> str:
        glossary = self.search(None, category) if category else self.get_glossary()
        data = CommentedMap()
        for cat in glossary.categories:
            if not cat.entries:
                continue
            terms = CommentedMap()
            for entry in cat.entries:
                body = CommentedMap()
                body["ko"] = entry.ko
                if entry.aliases:
                    body["aliases"] = CommentedSeq(entry.aliases)
                terms[entry.source] = body
            data[cat.name] = terms
        buf = StringIO()
        self._rt.dump(data, buf)
        return buf.getvalue()

    def _persist_category(self, category_name: str) -> None:
        path = self._category_files.get(category_name)
        if path is None:
            path = self._dir / DEFAULT_FILE
            self._category_files[category_name] = path
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = self._rt.load(f) or CommentedMap()
        else:
            data = CommentedMap()
        category = self._glossary.category(category_name)
        terms = CommentedMap()
        if category is not None:
            for entry in category.entries:
                body = CommentedMap()
                body["ko"] = entry.ko
                if entry.aliases:
                    body["aliases"] = CommentedSeq(entry.aliases)
                terms[entry.source] = body
        data[category_name] = terms
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            self._rt.dump(data, f)
