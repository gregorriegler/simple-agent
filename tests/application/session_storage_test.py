from simple_agent.application.session_storage import NoOpSessionStorage


def test_noop_session_storage_load_returns_empty_messages():
    storage = NoOpSessionStorage()

    messages = storage.load()

    assert len(messages) == 0


def test_noop_session_storage_save_returns_none():
    storage = NoOpSessionStorage()

    result = storage.save(storage.load())

    assert result is None
