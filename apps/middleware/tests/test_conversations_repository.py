import json
from pathlib import Path

import pytest

from translator_studio.conversations.repository import (
    ConversationNotFoundError,
    ConversationRepository,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_conversation.jsonl"


@pytest.fixture
def repo(tmp_path) -> ConversationRepository:
    return ConversationRepository(tmp_path / "conversations")


def test_import_export_roundtrip_preserves_llama_app_format(repo):
    original_lines = [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    session, messages = repo.import_jsonl(FIXTURE.read_text(encoding="utf-8"))

    assert session.id == "8b789483-d811-49c3-b8b7-e516a88dbdb4"
    assert session.name == "Token Generation"
    assert session.currNode == "87ae14cc-f4a4-4897-a0b6-ba0a33ac9b18"
    assert session.thinkingEnabled is True
    assert len(messages) == 3

    exported_lines = [
        json.loads(line) for line in repo.export_jsonl(session.id).splitlines()
    ]
    # Semantic equality, record by record (key order inside objects may differ).
    assert exported_lines == original_lines


def test_import_preserves_reasoning_timings_and_model(repo):
    _, messages = repo.import_jsonl(FIXTURE.read_text(encoding="utf-8"))
    assistant = next(m for m in messages if m.role == "assistant")
    assert assistant.model == "Serenity-12B-Q4_K_M.gguf"
    assert assistant.completionId == "chatcmpl-NJAso5Tuy0eEfJ47WZisG6PEKC9To53f"
    assert assistant.reasoningContent.startswith("The user has provided")
    assert assistant.timings is not None
    assert assistant.timings.predicted_n == 254
    assert assistant.timings.prompt_per_second == pytest.approx(744.21)


def test_tree_links_match_parent_children(repo):
    _, messages = repo.import_jsonl(FIXTURE.read_text(encoding="utf-8"))
    by_id = {m.id: m for m in messages}
    root = next(m for m in messages if m.type == "root")
    assert root.parent is None
    for message in messages:
        if message.parent is not None:
            assert message.id in by_id[message.parent].children


def test_create_conversation_makes_root_message(repo):
    session, messages = repo.create(name="New chat", system_prompt="SYS")
    assert session.name == "New chat"
    assert len(messages) == 1
    root = messages[0]
    assert root.type == "root"
    assert root.role == "system"
    assert root.content == "SYS"
    assert session.currNode == root.id
    # persisted and listed
    listed = repo.list()
    assert [s.id for s in listed] == [session.id]


def test_delete_removes_file(repo):
    session, _ = repo.create()
    assert repo.exists(session.id)
    repo.delete(session.id)
    assert not repo.exists(session.id)
    with pytest.raises(ConversationNotFoundError):
        repo.load(session.id)


def test_load_unknown_id_raises(repo):
    with pytest.raises(ConversationNotFoundError):
        repo.load("does-not-exist")


def test_import_rejects_payload_without_session(repo):
    with pytest.raises(ValueError):
        repo.import_jsonl('{"type":"message","message":{"id":"x","convId":"y","timestamp":1,"role":"user","content":"hi","parent":null,"children":[]}}')


def test_list_sorts_by_last_modified_desc(repo):
    older, _ = repo.create(name="older")
    newer, _ = repo.create(name="newer")
    older.lastModified = 1
    newer.lastModified = 2
    repo.save(older, repo.load(older.id)[1])
    repo.save(newer, repo.load(newer.id)[1])
    names = [s.name for s in repo.list()]
    assert names == ["newer", "older"]
