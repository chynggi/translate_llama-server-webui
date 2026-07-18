from __future__ import annotations

from dataclasses import dataclass, field

from ..glossary.models import Glossary, GlossaryEntry
from .matcher import find_matches


@dataclass
class DetectedEntry:
    entry: GlossaryEntry
    occurrences: int = 0


@dataclass
class DetectedGlossary:
    categories: dict[str, list[DetectedEntry]] = field(default_factory=dict)

    def total(self) -> int:
        return sum(len(entries) for entries in self.categories.values())

    def is_empty(self) -> bool:
        return self.total() == 0

    def to_response(self) -> dict:
        return {
            "categories": {
                name: [
                    {
                        "source": detected.entry.source,
                        "ko": detected.entry.ko,
                        "aliases": list(detected.entry.aliases),
                        "occurrences": detected.occurrences,
                    }
                    for detected in entries
                ]
                for name, entries in self.categories.items()
            },
            "total": self.total(),
        }


class DetectorService:
    def __init__(self, min_alias_length: int = 2, longest_match_first: bool = True):
        self._min_alias_length = min_alias_length
        self._longest_match_first = longest_match_first

    def configure(
        self, min_alias_length: int | None = None, longest_match_first: bool | None = None
    ) -> None:
        if min_alias_length is not None:
            self._min_alias_length = min_alias_length
        if longest_match_first is not None:
            self._longest_match_first = longest_match_first

    def detect(self, text: str, glossary: Glossary) -> DetectedGlossary:
        matches = find_matches(
            text, glossary, self._min_alias_length, self._longest_match_first
        )
        result = DetectedGlossary()
        category_order = {c.name: i for i, c in enumerate(glossary.categories)}
        seen: dict[tuple[str, str], DetectedEntry] = {}
        for match in matches:
            key = (match.category, match.entry.source)
            detected = seen.get(key)
            if detected is None:
                detected = DetectedEntry(entry=match.entry)
                seen[key] = detected
                result.categories.setdefault(match.category, []).append(detected)
            detected.occurrences += 1
        result.categories = dict(
            sorted(
                result.categories.items(),
                key=lambda item: category_order.get(item[0], len(category_order)),
            )
        )
        return result
