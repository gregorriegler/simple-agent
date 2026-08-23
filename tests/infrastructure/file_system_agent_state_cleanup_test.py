from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.file_system_agent_state_cleanup import (
    FileSystemAgentStateCleanup,
)


def test_cleanup_all_removes_todo_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".Agent.todos.md").write_text("todo", encoding="utf-8")
    (tmp_path / ".todos.md").write_text("root", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")

    cleanup = FileSystemAgentStateCleanup(tmp_path)

    cleanup.cleanup_all()

    assert not (tmp_path / ".Agent.todos.md").exists()
    assert not (tmp_path / ".todos.md").exists()
    assert (tmp_path / "keep.txt").exists()


def test_cleanup_all_removes_intent_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".Agent.intent.md").write_text("intent", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")

    cleanup = FileSystemAgentStateCleanup(tmp_path)

    cleanup.cleanup_all()

    assert not (tmp_path / ".Agent.intent.md").exists()
    assert (tmp_path / "keep.txt").exists()


def test_cleanup_for_agent_removes_todo_and_intent_of_that_agent(tmp_path):
    (tmp_path / ".Agent.todos.md").write_text("todo", encoding="utf-8")
    (tmp_path / ".Agent.intent.md").write_text("intent", encoding="utf-8")
    (tmp_path / ".Other.intent.md").write_text("other", encoding="utf-8")

    cleanup = FileSystemAgentStateCleanup(tmp_path)

    cleanup.cleanup_for_agent(AgentId("Agent", root=tmp_path))

    assert not (tmp_path / ".Agent.todos.md").exists()
    assert not (tmp_path / ".Agent.intent.md").exists()
    assert (tmp_path / ".Other.intent.md").exists()
