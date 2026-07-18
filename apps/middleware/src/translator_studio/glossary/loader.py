from __future__ import annotations

from pathlib import Path

from ..utils import yaml_io
from .models import Glossary, GlossaryCategory, GlossaryEntry


def parse_glossary_data(data: dict) -> dict[str, dict[str, GlossaryEntry]]:
    """Normalize a raw YAML mapping into {category: {source: GlossaryEntry}}."""
    merged: dict[str, dict[str, GlossaryEntry]] = {}
    if not isinstance(data, dict):
        return merged
    for category, terms in data.items():
        if not isinstance(terms, dict):
            continue
        bucket = merged.setdefault(str(category), {})
        for source, body in terms.items():
            body = body or {}
            if not isinstance(body, dict):
                body = {"ko": str(body)}
            bucket[str(source)] = GlossaryEntry(
                source=str(source),
                ko=str(body.get("ko", "")),
                aliases=[str(a) for a in (body.get("aliases") or [])],
            )
    return merged


def load_glossary_file(path: str | Path) -> dict[str, dict[str, GlossaryEntry]]:
    return parse_glossary_data(yaml_io.read_yaml(path) or {})


def load_glossary_dir(directory: str | Path) -> Glossary:
    """Merge every *.yaml / *.yml in the directory into one Glossary.

    Categories come from top-level YAML keys, so new categories and new files
    require zero code changes.
    """
    directory = Path(directory)
    merged: dict[str, dict[str, GlossaryEntry]] = {}
    if directory.exists():
        files = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))
        for path in files:
            for category, entries in load_glossary_file(path).items():
                merged.setdefault(category, {}).update(entries)
    return Glossary(
        categories=[
            GlossaryCategory(name=category, entries=list(entries.values()))
            for category, entries in merged.items()
        ]
    )
