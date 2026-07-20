from fastapi.testclient import TestClient

from translator_studio.config import GenerationSettings
from translator_studio.main import create_app


def _client(services, settings) -> TestClient:
    return TestClient(create_app(settings=settings, services=services))


def test_to_payload_params_omits_unset_values():
    assert GenerationSettings().to_payload_params() == {"repeat_penalty": 1.15}
    gen = GenerationSettings(temperature=0.7, top_k=40, repeat_penalty=None)
    assert gen.to_payload_params() == {"temperature": 0.7, "top_k": 40}


async def test_translate_payload_merges_generation_defaults(services, fake_llama):
    services.settings.generation.temperature = 0.9
    await services.translation.translate("空崎ヒナ", "bluearchive")
    payload = fake_llama.last_payload
    assert payload["repeat_penalty"] == 1.15  # server default applied
    assert payload["temperature"] == 0.3  # preset value wins over server default


async def test_translate_request_params_override_generation(services, fake_llama):
    await services.translation.translate(
        "空崎ヒナ", "bluearchive", params={"repeat_penalty": 1.3}
    )
    assert fake_llama.last_payload["repeat_penalty"] == 1.3


def test_proxy_passthrough_merges_defaults_but_body_wins(services, settings, fake_llama):
    with _client(services, settings) as client:
        client.post(
            "/v1/chat/completions",
            json={
                "model": "fake-model",
                "messages": [{"role": "user", "content": "hi"}],
                "repeat_penalty": 1.05,
            },
        )
        assert fake_llama.last_payload["repeat_penalty"] == 1.05  # caller wins

        client.post(
            "/v1/chat/completions",
            json={"model": "fake-model", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert fake_llama.last_payload["repeat_penalty"] == 1.15  # default filled in


async def test_stream_done_carries_reasoning_and_timings(services, fake_llama):
    fake_llama.stream_lines = [
        'data: {"choices": [{"delta": {"reasoning_content": "생각 중..."}}]}',
        'data: {"choices": [{"delta": {"content": "번역문"}}], "timings": {"predicted_n": 7}}',
        "data: [DONE]",
    ]
    chunks = []
    async for chunk in services.translation.translate_stream("空崎ヒナ", "bluearchive"):
        chunks.append(chunk)
    text = b"".join(chunks).decode("utf-8")
    assert '"type": "reasoning"' in text
    assert "생각 중..." in text
    assert '"reasoning_content": "생각 중..."' in text
    assert '"timings": {"predicted_n": 7}' in text


def test_settings_api_exposes_and_updates_generation(services, settings):
    with _client(services, settings) as client:
        current = client.get("/settings").json()
        assert current["generation"]["repeat_penalty"] == 1.15
        assert current["chat"]["enable_thinking"] is False

        updated = client.put(
            "/settings",
            json={
                "generation": {"temperature": 0.8, "top_k": 40},
                "chat": {"enable_thinking": True},
                "persist": False,
            },
        )
        assert updated.status_code == 200
        body = updated.json()
        assert body["generation"]["temperature"] == 0.8
        assert body["generation"]["top_k"] == 40
        assert body["generation"]["repeat_penalty"] == 1.15  # untouched
        assert body["chat"]["enable_thinking"] is True

        # explicit null clears a value
        cleared = client.put(
            "/settings",
            json={"generation": {"repeat_penalty": None}, "persist": False},
        )
        assert cleared.json()["generation"]["repeat_penalty"] is None


def test_settings_persist_writes_generation_and_chat(services, settings):
    with _client(services, settings) as client:
        client.put(
            "/settings",
            json={
                "generation": {"min_p": 0.05, "repeat_penalty": None},
                "chat": {"enable_thinking": True},
                "persist": True,
            },
        )
    text = services.config_path.read_text(encoding="utf-8")
    assert "min_p: 0.05" in text
    assert "repeat_penalty" not in text  # cleared values stay out of the YAML
    assert "enable_thinking: true" in text
