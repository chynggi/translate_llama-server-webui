from translator_studio.glossary.loader import load_glossary_dir


def test_loads_categories_and_entries(settings):
    glossary = load_glossary_dir(settings.paths.glossary_dir)
    assert glossary.category_names() == ["students", "locations", "organizations"]
    students = glossary.category("students")
    assert students is not None
    hina = students.find("空崎ヒナ")
    assert hina is not None
    assert hina.ko == "소라사키 히나"
    assert hina.aliases == ["ヒナ"]


def test_merges_entries_across_files(tmp_path):
    glossary_dir = tmp_path / "glossary"
    glossary_dir.mkdir()
    (glossary_dir / "a.yaml").write_text(
        "students:\n  空崎ヒナ:\n    ko: 소라사키 히나\n", encoding="utf-8"
    )
    (glossary_dir / "b.yaml").write_text(
        "students:\n  陸八魔アル:\n    ko: 리쿠하치마 아루\n", encoding="utf-8"
    )
    glossary = load_glossary_dir(glossary_dir)
    students = glossary.category("students")
    assert students is not None
    sources = {e.source for e in students.entries}
    assert sources == {"空崎ヒナ", "陸八魔アル"}


def test_new_top_level_key_becomes_category_without_code_change(tmp_path):
    glossary_dir = tmp_path / "glossary"
    glossary_dir.mkdir()
    (glossary_dir / "custom.yaml").write_text(
        "weapons:\n  エクスカリバー:\n    ko: 엑스칼리버\n", encoding="utf-8"
    )
    glossary = load_glossary_dir(glossary_dir)
    assert glossary.category("weapons") is not None


def test_empty_dir_returns_empty_glossary(tmp_path):
    glossary = load_glossary_dir(tmp_path / "empty")
    assert glossary.categories == []
