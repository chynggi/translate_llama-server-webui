import pytest


async def test_translate_non_stream(services, fake_llama):
    result = await services.translation.translate(
        "空崎ヒナがゲヘナに向かった。", "bluearchive"
    )
    assert result.output == "히나: 아루, 가자."
    assert result.model == "fake-model"
    assert result.preset == "bluearchive"
    assert result.detected["total"] == 2
    assert result.tokens["total_tokens"] == 15
    # llama.cpp received the assembled prompt with only the used glossary injected
    payload = fake_llama.last_payload
    system = payload["messages"][0]["content"]
    assert "空崎ヒナ = 소라사키 히나" in system
    assert "ゲヘナ = 게헨나" in system
    assert "陸八魔アル" not in system
    assert payload["model"] == "fake-model"
    assert payload["stream"] is False


async def test_translate_unknown_preset_raises(services):
    with pytest.raises(KeyError):
        await services.translation.translate("テスト", "nope")


async def test_translate_stream_yields_delta_then_done(services):
    chunks = []
    async for chunk in services.translation.translate_stream("空崎ヒナ", "bluearchive"):
        chunks.append(chunk)
    text = b"".join(chunks).decode("utf-8")
    assert '"type": "delta"' in text
    assert '"type": "done"' in text
    assert "히나: 아루, 가자." in text


async def test_translate_logs_record(services):
    await services.translation.translate("空崎ヒナ", "bluearchive")
    logs = services.logger.list()
    assert logs["total"] == 1
    record = logs["items"][0]
    assert record["preset"] == "bluearchive"
    assert record["output"] == "히나: 아루, 가자."
    assert record["prompt"]
    assert record["detected"]["total"] == 1
    assert record["source"] == "空崎ヒナ"


async def test_preview_returns_messages_and_token_count(services):
    preview = await services.translation.preview(
        "空崎ヒナがゲヘナに向かった。", "bluearchive"
    )
    assert preview.messages[0]["role"] == "system"
    assert preview.token_count > 0
    assert preview.detected["total"] == 2
    assert preview.model == "fake-model"
    assert "空崎ヒナ = 소라사키 히나" in preview.parts.glossary
