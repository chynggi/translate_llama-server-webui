from __future__ import annotations

from dataclasses import dataclass

from ..glossary.models import Glossary, GlossaryEntry


@dataclass(frozen=True)
class Match:
    category: str
    entry: GlossaryEntry
    surface: str
    start: int
    end: int


def _iter_surfaces(entry: GlossaryEntry):
    yield entry.source
    for alias in entry.aliases:
        if alias and alias != entry.source:
            yield alias


def find_matches(
    text: str,
    glossary: Glossary,
    min_alias_length: int = 2,
    longest_match_first: bool = True,
) -> list[Match]:
    """Find glossary occurrences in source text.

    Japanese has no spaces, so matching is substring-based. Overlaps are
    resolved by preferring longer terms (e.g. ``空崎ヒナ`` over its alias
    ``ヒナ``), then earliest position.
    """
    if not text:
        return []
    candidates: list[Match] = []
    for category in glossary.categories:
        for entry in category.entries:
            for surface in _iter_surfaces(entry):
                if not surface:
                    continue
                is_alias = surface != entry.source
                if is_alias and len(surface) < min_alias_length:
                    continue
                start = text.find(surface)
                while start != -1:
                    candidates.append(
                        Match(category.name, entry, surface, start, start + len(surface))
                    )
                    start = text.find(surface, start + len(surface))
    if not candidates:
        return []
    if longest_match_first:
        candidates.sort(key=lambda m: (-(m.end - m.start), m.start))
    else:
        candidates.sort(key=lambda m: (m.start, -(m.end - m.start)))
    chosen: list[Match] = []
    occupied: list[tuple[int, int]] = []
    for match in candidates:
        if any(match.start < end and match.end > start for start, end in occupied):
            continue
        chosen.append(match)
        occupied.append((match.start, match.end))
    chosen.sort(key=lambda m: (m.start, m.end))
    return chosen
