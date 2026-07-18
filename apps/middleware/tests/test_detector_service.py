from translator_studio.detector.service import DetectorService

from .conftest import make_glossary


def test_detect_groups_by_category_and_counts_occurrences():
    detector = DetectorService()
    detected = detector.detect("ヒナと空崎ヒナがゲヘナへ。ヒナ。", make_glossary())
    assert detected.categories["students"][0].entry.source == "空崎ヒナ"
    # 空崎ヒナ appears once as full term + twice via alias ヒナ
    assert detected.categories["students"][0].occurrences == 3
    assert detected.categories["locations"][0].entry.source == "ゲヘナ"
    assert detected.total() == 2


def test_detect_empty_when_nothing_matches():
    detector = DetectorService()
    detected = detector.detect("아무 관련 없는 문장.", make_glossary())
    assert detected.is_empty()


def test_to_response_shape():
    detector = DetectorService()
    detected = detector.detect("空崎ヒナ", make_glossary())
    response = detected.to_response()
    assert response["total"] == 1
    entry = response["categories"]["students"][0]
    assert entry["source"] == "空崎ヒナ"
    assert entry["ko"] == "소라사키 히나"
    assert entry["occurrences"] == 1
