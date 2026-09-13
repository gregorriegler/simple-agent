from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.file_intents import FileIntents


def test_reads_the_communicated_intent(tmp_path):
    agent_id = AgentId("Agent").with_root(tmp_path)
    agent_id.intent_filename().write_text("Store the greeting")

    assert FileIntents().read(agent_id) == "Store the greeting"


def test_nothing_was_communicated_yet(tmp_path):
    agent_id = AgentId("Agent").with_root(tmp_path)

    assert FileIntents().read(agent_id) == ""


def test_the_written_intent_is_read_back(tmp_path):
    agent_id = AgentId("Agent").with_root(tmp_path)
    intents = FileIntents()

    intents.write(agent_id, "Store the greeting")

    assert intents.read(agent_id) == "Store the greeting"
