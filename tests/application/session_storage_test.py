from simple_agent.application.agent_id import AgentId
from simple_agent.application.session_storage import NoOpSessionStorage


def test_noop_session_storage_load_returns_empty_messages():
    storage = NoOpSessionStorage()

    messages = storage.load_messages(AgentId("Agent"))

    assert len(messages) == 0


def test_noop_session_storage_save_returns_none():
    storage = NoOpSessionStorage()

    agent_id = AgentId("Agent")

    result = storage.save_messages(agent_id, storage.load_messages(agent_id))

    assert result is None
