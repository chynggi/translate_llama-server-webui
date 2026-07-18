from translator_studio.glossary.loader import load_glossary_file
from translator_studio.glossary.repository import GlossaryRepository


def test_upsert_adds_and_persists(tmp_path):
    repo = GlossaryRepository(tmp_path)
    repo.upsert("students", _entry("空崎ヒナ", "소라사키 히나", ["ヒナ"]))
    on_disk = load_glossary_file(tmp_path / "custom.yaml")
    assert on_disk["students"]["空崎ヒナ"].ko == "소라사키 히나"


def test_upsert_updates_existing(tmp_path):
    repo = GlossaryRepository(tmp_path)
    repo.upsert("students", _entry("空崎ヒナ", "소라사키 히나"))
    repo.upsert("students", _entry("空崎ヒナ", "소라사키 히나(수정)"))
    entry = repo.get_glossary().category("students").find("空崎ヒナ")
    assert entry.ko == "소라사키 히나(수정)"
    assert len(repo.get_glossary().category("students").entries) == 1


def test_import_yaml_merges(tmp_path):
    repo = GlossaryRepository(tmp_path)
    counts = repo.import_yaml(
        "students:\n  陸八魔アル:\n    ko: 리쿠하치마 아루\n"
        "locations:\n  ゲヘナ:\n    ko: 게헨나\n"
    )
    assert counts == {"students": 1, "locations": 1}
    assert repo.get_glossary().category("locations").find("ゲヘナ").ko == "게헨나"


def test_upsert_writes_back_to_originating_category_file(tmp_path):
    (tmp_path / "bluearchive.yaml").write_text(
        "students:\n  空崎ヒナ:\n    ko: 소라사키 히나\n", encoding="utf-8"
    )
    repo = GlossaryRepository(tmp_path)
    repo.upsert("students", _entry("陸八魔アル", "리쿠하치마 아루"))
    on_disk = load_glossary_file(tmp_path / "bluearchive.yaml")
    assert "陸八魔アル" in on_disk["students"]
    assert "空崎ヒナ" in on_disk["students"]  # existing entry preserved


def test_search_filters_by_query_and_category(tmp_path):
    repo = GlossaryRepository(tmp_path)
    repo.upsert("students", _entry("空崎ヒナ", "소라사키 히나"))
    repo.upsert("locations", _entry("ゲヘナ", "게헨나"))
    result = repo.search("ヒナ")
    assert result.category("students") is not None
    assert result.category("locations").entries == []
    by_category = repo.search(None, category="locations")
    assert by_category.category("students") is None  # filtered out entirely
    assert len(by_category.category("locations").entries) == 1


def test_export_yaml_round_trip(tmp_path):
    repo = GlossaryRepository(tmp_path)
    repo.upsert("students", _entry("空崎ヒナ", "소라사키 히나", ["ヒナ"]))
    repo.upsert("locations", _entry("ゲヘナ", "게헨나"))
    exported = repo.export_yaml()
    assert "空崎ヒナ" in exported
    assert "소라사키 히나" in exported
    assert "ゲヘナ" in exported
    students_only = repo.export_yaml(category="students")
    assert "空崎ヒナ" in students_only
    assert "ゲヘナ" not in students_only


def _entry(source, ko, aliases=None):

    from translator_studio.glossary.models import GlossaryEntry

    return GlossaryEntry(source=source, ko=ko, aliases=aliases or [])
