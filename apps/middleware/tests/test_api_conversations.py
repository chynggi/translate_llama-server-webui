import json
from pathlib import Path

from fastapi.testclient import TestClient

from translator_studio.main import create_app

FIXTURE = Path(__file__).parent / "fixtures" / "sample_conversation.jsonl"


def _client(services, settings) -> TestClient:
    return TestClient(create_app(settings=settings, services=services))


def test_conversation_crud_flow(services, settings):
    with _client(services, settings) as client:
        created = client.post("/conversations", json={"name": "번역 채팅"})
        assert created.status_code == 201
        body = created.json()
        session = body["session"]
        assert session["name"] == "번역 채팅"
        assert len(body["messages"]) == 1
        root = body["messages"][0]
        assert root["type"] == "root"
        assert root["role"] == "system"
        assert session["currNode"] == root["id"]

        listed = client.get("/conversations")
        assert listed.status_code == 200
        assert [c["id"] for c in listed.json()["conversations"]] == [session["id"]]

        fetched = client.get(f"/conversations/{session['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["session"]["id"] == session["id"]

        renamed = client.patch(
            f"/conversations/{session['id']}", json={"name": "새 이름"}
        )
        assert renamed.status_code == 200
        assert renamed.json()["session"]["name"] == "새 이름"

        deleted = client.delete(f"/conversations/{session['id']}")
        assert deleted.status_code == 200
        assert client.get(f"/conversations/{session['id']}").status_code == 404


def test_append_message_and_branch_via_api(services, settings):
    with _client(services, settings) as client:
        session = client.post("/conversations", json={}).json()["session"]
        conv = client.get(f"/conversations/{session['id']}").json()
        root_id = conv["messages"][0]["id"]

        user = client.post(
            f"/conversations/{session['id']}/messages",
            json={"parent": root_id, "role": "user", "content": "空崎ヒナがゲヘナへ"},
        )
        assert user.status_code == 201
        user_msg = user.json()["message"]
        assert user.json()["session"]["currNode"] == user_msg["id"]

        for text in ("응답 A", "응답 B"):
            response = client.post(
                f"/conversations/{session['id']}/messages",
                json={
                    "parent": user_msg["id"],
                    "role": "assistant",
                    "content": text,
                    "model": "fake-model",
                },
            )
            assert response.status_code == 201

        conv = client.get(f"/conversations/{session['id']}").json()
        by_id = {m["id"]: m for m in conv["messages"]}
        assert len(by_id[user_msg["id"]]["children"]) == 2

        bad = client.post(
            f"/conversations/{session['id']}/messages",
            json={"parent": "missing", "role": "user", "content": "x"},
        )
        assert bad.status_code == 400


def test_import_export_roundtrip_via_api(services, settings):
    original = FIXTURE.read_text(encoding="utf-8")
    with _client(services, settings) as client:
        imported = client.post("/conversations/import", json={"jsonl": original})
        assert imported.status_code == 201
        session = imported.json()["session"]
        assert session["name"] == "Token Generation"

        exported = client.get(f"/conversations/{session['id']}/export")
        assert exported.status_code == 200
        assert exported.headers["content-type"].startswith("application/x-ndjson")
        assert [json.loads(l) for l in exported.text.splitlines()] == [
            json.loads(l) for l in original.splitlines() if l.strip()
        ]


def test_import_invalid_jsonl_returns_400(services, settings):
    with _client(services, settings) as client:
        response = client.post("/conversations/import", json={"jsonl": "{}"})
        assert response.status_code == 400


def test_chat_system_prompt_endpoint(services, settings):
    with _client(services, settings) as client:
        response = client.get("/chat/system-prompt")
        assert response.status_code == 200
        body = response.json()
        assert body["file"] == "chat_system.md"
        # conftest prompts dir has no chat_system.md -> empty content
        assert body["content"] == ""
