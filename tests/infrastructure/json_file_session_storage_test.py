import json

from simple_agent.application.llm import Messages
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage


def test_load_returns_empty_messages_when_file_missing(tmp_path):
    storage = JsonFileSessionStorage(str(tmp_path / "missing.json"))

    messages = storage.load()

    assert len(messages) == 0


def test_load_reads_list_data(tmp_path):
    path = tmp_path / "session.json"
    path.write_text(json.dumps([{"role": "user", "content": "hi"}]), encoding="utf-8")
    storage = JsonFileSessionStorage(str(path))

    messages = storage.load()

    assert messages.to_list() == [{"role": "user", "content": "hi"}]


def test_load_returns_empty_messages_for_invalid_json(tmp_path, capsys):
    path = tmp_path / "session.json"
    path.write_text("{broken", encoding="utf-8")
    storage = JsonFileSessionStorage(str(path))

    messages = storage.load()

    assert len(messages) == 0
    assert "Warning: Could not load session file" in capsys.readouterr().err


def test_save_warns_when_write_fails(tmp_path, capsys):
    path = tmp_path / "missing" / "session.json"
    storage = JsonFileSessionStorage(str(path))

    storage.save(Messages())

    assert "Warning: Could not save session file" in capsys.readouterr().err
