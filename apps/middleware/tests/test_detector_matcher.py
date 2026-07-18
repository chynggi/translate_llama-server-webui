from translator_studio.detector.matcher import find_matches
from translator_studio.glossary.models import Glossary, GlossaryCategory, GlossaryEntry

from .conftest import make_glossary


def test_detects_source_term():
    matches = find_matches("空崎ヒナが現れた。", make_glossary())
    assert [m.entry.ko for m in matches] == ["소라사키 히나"]


def test_detects_alias():
    matches = find_matches("ヒナ、行くよ。", make_glossary())
    assert any(m.surface == "ヒナ" and m.entry.source == "空崎ヒナ" for m in matches)


def test_longest_match_wins_over_alias():
    # Both 空崎ヒナ (4 chars) and its alias ヒナ (2 chars) match; only the
    # longest should occupy the overlapping span.
    matches = find_matches("空崎ヒナはヒナと呼ばれる。", make_glossary())
    spans = [(m.start, m.end) for m in matches]
    assert (0, 4) in spans  # 空崎ヒナ
    surfaces = [m.surface for m in matches]
    assert "ヒナ" in surfaces  # second occurrence still matched via alias


def test_no_overlapping_double_count():
    matches = find_matches("空崎ヒナ", make_glossary())
    occupied = [(m.start, m.end) for m in matches]
    for i, (s1, e1) in enumerate(occupied):
        for s2, e2 in occupied[i + 1 :]:
            assert e1 <= s2 or e2 <= s1, "matches must not overlap"


def test_min_alias_length_guard():
    glossary = Glossary(
        categories=[
            GlossaryCategory(
                name="students",
                entries=[GlossaryEntry(source="空崎ヒナ", ko="소라사키 히나", aliases=["ナ"])],
            )
        ]
    )
    # 1-char alias below the default min length of 2 is ignored.
    assert find_matches("ナ", glossary, min_alias_length=2) == []
    assert find_matches("ナ", glossary, min_alias_length=1) != []


def test_no_match_returns_empty():
    assert find_matches("関係ない文章。", make_glossary()) == []


def test_empty_text_returns_empty():
    assert find_matches("", make_glossary()) == []


def test_multiple_categories_detected():
    matches = find_matches("空崎ヒナがゲヘナに向かった。", make_glossary())
    categories = {m.category for m in matches}
    assert categories == {"students", "locations"}


def test_matches_sorted_by_position():
    matches = find_matches("ゲヘナの空崎ヒナ", make_glossary())
    starts = [m.start for m in matches]
    assert starts == sorted(starts)
