import pytest

from translator_studio.conversations.repository import ConversationRepository
from translator_studio.conversations.service import (
    ConversationService,
    ParentNotFoundError,
    active_path,
    descend_to_leaf,
    siblings_of,
)


@pytest.fixture
def service(tmp_path) -> ConversationService:
    return ConversationService(ConversationRepository(tmp_path / "conversations"))


def test_append_message_links_parent_and_moves_curr_node(service):
    session, messages = service.create(name="chat")
    root = messages[0]
    session, user = service.append_message(
        session.id, parent=root.id, role="user", content="안녕"
    )
    assert session.currNode == user.id
    _, stored_messages = service.get(session.id)
    stored_root = next(m for m in stored_messages if m.id == root.id)
    assert stored_root.children == [user.id]

    session, assistant = service.append_message(
        session.id,
        parent=user.id,
        role="assistant",
        content="반갑습니다",
        model="fake-model",
        reasoning_content="thinking...",
        timings={"predicted_n": 3, "predicted_per_second": 12.5},
    )
    assert session.currNode == assistant.id
    assert assistant.reasoningContent == "thinking..."
    assert assistant.timings.predicted_n == 3


def test_append_to_unknown_parent_raises(service):
    session, _ = service.create()
    with pytest.raises(ParentNotFoundError):
        service.append_message(session.id, parent="nope", role="user", content="x")


def test_branching_creates_siblings_and_active_path(service):
    session, messages = service.create()
    root_id = messages[0].id
    _, user = service.append_message(session.id, parent=root_id, role="user", content="q")
    _, answer_a = service.append_message(
        session.id, parent=user.id, role="assistant", content="A", timestamp=1000
    )
    # regenerate: second assistant child under the same user message
    _, answer_b = service.append_message(
        session.id, parent=user.id, role="assistant", content="B", timestamp=2000
    )
    _, stored = service.get(session.id)

    siblings = siblings_of(stored, answer_a.id)
    assert {m.id for m in siblings} == {answer_a.id, answer_b.id}

    path = active_path(stored, answer_b.id)
    assert [m.role for m in path] == ["system", "user", "assistant"]
    assert path[-1].content == "B"

    # branch switching descends to the newest leaf of the chosen branch
    leaf = descend_to_leaf(stored, user.id)
    assert leaf.id == answer_b.id  # newest timestamp wins
    leaf = descend_to_leaf(stored, answer_a.id)
    assert leaf.id == answer_a.id


def test_update_session_rename_and_curr_node(service):
    session, messages = service.create()
    root_id = messages[0].id
    _, user = service.append_message(session.id, parent=root_id, role="user", content="q")
    updated = service.update_session(session.id, name="renamed", curr_node=root_id)
    assert updated.name == "renamed"
    assert updated.currNode == root_id
    with pytest.raises(ParentNotFoundError):
        service.update_session(session.id, curr_node="missing")


def test_export_import_via_service(service, tmp_path):
    session, messages = service.create(name="export me")
    _, user = service.append_message(
        session.id, parent=messages[0].id, role="user", content="원문"
    )
    service.append_message(session.id, parent=user.id, role="assistant", content="번역")
    text = service.export_jsonl(session.id)
    assert '"type":"session"' in text.replace(" ", "") or '"type": "session"' in text

    other = ConversationService(ConversationRepository(tmp_path / "other"))
    imported_session, imported_messages = other.import_jsonl(text)
    assert imported_session.id == session.id
    assert len(imported_messages) == 3
