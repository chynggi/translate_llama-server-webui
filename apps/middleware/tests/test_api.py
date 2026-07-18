from fastapi.testclient import TestClient

from translator_studio.main import create_app


def _client(services, settings) -> TestClient:
    return TestClient(create_app(settings=settings, services=services))


def test_healthz(services, settings):
    with _client(services, settings) as client:
        assert client.get("/healthz").status_code == 200


def test_list_models(services, settings):
    with _client(services, settings) as client:
        response = client.get("/v1/models")
        assert response.status_code == 200
        assert response.json()["data"][0]["id"] == "fake-model"


def test_translate_endpoint(services, settings):
    with _client(services, settings) as client:
        response = client.post(
            "/translate", json={"source": "空崎ヒナ", "preset": "bluearchive"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["output"] == "히나: 아루, 가자."
        assert body["detected"]["total"] == 1
        assert body["model"] == "fake-model"


def test_translate_stream_endpoint(services, settings):
    with _client(services, settings) as client:
        response = client.post(
            "/translate",
            json={"source": "空崎ヒナ", "preset": "bluearchive", "stream": True},
        )
        assert response.status_code == 200
        assert "data:" in response.text
        assert '"type": "done"' in response.text


def test_translate_unknown_preset_returns_404(services, settings):
    with _client(services, settings) as client:
        response = client.post("/translate", json={"source": "x", "preset": "nope"})
        assert response.status_code == 404


def test_preview_endpoint(services, settings):
    with _client(services, settings) as client:
        response = client.post(
            "/preview", json={"source": "空崎ヒナ", "preset": "bluearchive"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_count"] > 0
        assert body["messages"][0]["role"] == "system"
        assert body["detected"]["total"] == 1


def test_presets_endpoints(services, settings):
    with _client(services, settings) as client:
        listing = client.get("/presets")
        assert listing.status_code == 200
        assert any(p["id"] == "bluearchive" for p in listing.json()["presets"])
        assert client.get("/presets/bluearchive").status_code == 200
        assert client.get("/presets/nope").status_code == 404


def test_glossary_get_search(services, settings):
    with _client(services, settings) as client:
        response = client.get("/glossary")
        assert response.status_code == 200
        assert response.json()["total_entries"] >= 1
        filtered = client.get("/glossary", params={"q": "ヒナ"})
        assert filtered.status_code == 200
        categories = {c["name"] for c in filtered.json()["categories"] if c["entries"]}
        assert categories == {"students"}


def test_glossary_upsert_and_import(services, settings):
    with _client(services, settings) as client:
        upsert = client.post(
            "/glossary",
            json={
                "action": "upsert",
                "category": "students",
                "source": "新キャラ",
                "ko": "신 캐릭터",
            },
        )
        assert upsert.status_code == 200
        assert upsert.json()["source"] == "新キャラ"
        imported = client.post(
            "/glossary",
            json={"action": "import", "yaml": "items:\n  剣:\n    ko: 검\n"},
        )
        assert imported.status_code == 200
        assert imported.json()["imported"]["items"] == 1


def test_glossary_bad_action_returns_400(services, settings):
    with _client(services, settings) as client:
        response = client.post("/glossary", json={"action": "bogus"})
        assert response.status_code == 400


def test_logs_endpoint(services, settings):
    with _client(services, settings) as client:
        client.post("/translate", json={"source": "空崎ヒナ", "preset": "bluearchive"})
        response = client.get("/logs")
        assert response.status_code == 200
        assert response.json()["total"] >= 1
        assert response.json()["items"][0]["preset"] == "bluearchive"


def test_chat_completions_passthrough_without_preset(services, settings, fake_llama):
    with _client(services, settings) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "fake-model",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            },
        )
        assert response.status_code == 200
        assert fake_llama.last_payload["messages"][0]["content"] == "hello"


def test_chat_completions_enriches_when_preset_present(services, settings, fake_llama):
    with _client(services, settings) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "fake-model",
                "preset": "bluearchive",
                "messages": [{"role": "user", "content": "空崎ヒナがゲヘナへ"}],
                "stream": False,
            },
        )
        assert response.status_code == 200
        payload = fake_llama.last_payload
        assert payload["messages"][0]["role"] == "system"
        system = payload["messages"][0]["content"]
        assert "空崎ヒナ = 소라사키 히나" in system
        assert "ゲヘナ = 게헨나" in system
        assert "陸八魔アル" not in system


def test_glossary_export(services, settings):
    with _client(services, settings) as client:
        response = client.get("/glossary/export")
        assert response.status_code == 200
        assert "空崎ヒナ" in response.text
        assert "소라사키 히나" in response.text


def test_settings_get_and_update(services, settings, fake_llama, tmp_path):
    with _client(services, settings) as client:
        current = client.get("/settings")
        assert current.status_code == 200
        assert current.json()["detector"]["min_alias_length"] == 2

        updated = client.put(
            "/settings",
            json={
                "llama_server": {"base_url": "http://llama.local:9090", "default_model": "m1"},
                "detector": {"min_alias_length": 3},
                "persist": True,
            },
        )
        assert updated.status_code == 200
        body = updated.json()
        assert body["llama_server"]["base_url"] == "http://llama.local:9090"
        assert body["llama_server"]["default_model"] == "m1"
        assert body["detector"]["min_alias_length"] == 3
        assert fake_llama.reconfigured["base_url"] == "http://llama.local:9090"
        assert (tmp_path / "config.yaml").exists()
