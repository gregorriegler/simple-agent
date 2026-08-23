from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.file_intent import FileIntent


def test_reads_the_communicated_intent(tmp_path):
    agent_id = AgentId("Agent").with_root(tmp_path)
    agent_id.intent_filename().write_text("Store the greeting")

    assert FileIntent(agent_id).read() == "Store the greeting"


def test_nothing_was_communicated_yet(tmp_path):
    agent_id = AgentId("Agent").with_root(tmp_path)

    assert FileIntent(agent_id).read() == ""
