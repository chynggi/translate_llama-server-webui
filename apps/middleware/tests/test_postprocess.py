from translator_studio.postprocess.service import Postprocessor


def test_strips_surrounding_whitespace():
    assert Postprocessor().process("  안녕하세요 \n") == "안녕하세요"


def test_strips_code_fence():
    assert Postprocessor().process("```\n번역문\n```") == "번역문"
    assert Postprocessor().process("```text\n번역문\n```") == "번역문"


def test_none_and_empty():
    assert Postprocessor().process(None) == ""
    assert Postprocessor().process("") == ""


def test_plain_text_unchanged():
    assert Postprocessor().process("그냥 문장.") == "그냥 문장."
