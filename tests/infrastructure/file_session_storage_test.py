import json
import os

from simple_agent.application.agent_id import AgentId
from simple_agent.application.llm import Messages
from simple_agent.infrastructure.file_session_storage import FileSessionStorage


def test_save_and_load_messages_per_agent(tmp_path):
    storage = FileSessionStorage.create(
        tmp_path / "sessions",
        continue_session=False,
        cwd=tmp_path,
    )
    agent_id = AgentId("Agent", root=storage.session_root())
    subagent_id = AgentId("Agent/Sub", root=storage.session_root())

    agent_messages = Messages([{"role": "user", "content": "hello"}])
    subagent_messages = Messages([{"role": "assistant", "content": "hi"}])

    storage.save_messages(agent_id, agent_messages)
    storage.save_messages(subagent_id, subagent_messages)

    assert storage.load_messages(agent_id).to_list() == agent_messages.to_list()
    assert storage.load_messages(subagent_id).to_list() == subagent_messages.to_list()


def test_continue_session_uses_latest_session_directory(tmp_path):
    base_dir = tmp_path / "sessions"
    storage_a = FileSessionStorage.create(
        base_dir,
        continue_session=False,
        cwd=tmp_path,
    )
    storage_b = FileSessionStorage.create(
        base_dir,
        continue_session=False,
        cwd=tmp_path,
    )

    os.utime(storage_a.session_root(), (1, 1))
    os.utime(storage_b.session_root(), (2, 2))

    continued = FileSessionStorage.create(
        base_dir,
        continue_session=True,
        cwd=tmp_path,
    )

    assert continued.session_root() == storage_b.session_root()


def test_session_manifest_written(tmp_path):
    storage = FileSessionStorage.create(
        tmp_path / "sessions",
        continue_session=False,
        cwd=tmp_path,
    )

    manifest_path = storage.session_root() / "manifest.json"

    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["session_id"] == storage.session_root().name


def test_load_messages_returns_empty_for_unknown_agent(tmp_path):
    storage = FileSessionStorage.create(
        tmp_path / "sessions",
        continue_session=False,
        cwd=tmp_path,
    )
    agent_id = AgentId("NeverSaved", root=storage.session_root())

    messages = storage.load_messages(agent_id)

    assert len(messages) == 0


def test_continue_session_creates_new_when_no_sessions_exist(tmp_path):
    base_dir = tmp_path / "sessions"

    storage = FileSessionStorage.create(base_dir, continue_session=True, cwd=tmp_path)

    assert storage.session_root().exists()
