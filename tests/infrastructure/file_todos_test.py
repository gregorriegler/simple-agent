from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.file_todos import FileTodos


def test_nothing_was_planned_yet(tmp_path):
    agent_id = AgentId("Agent").with_root(tmp_path)

    assert FileTodos().read(agent_id) == ""


def test_the_written_todos_are_read_back(tmp_path):
    agent_id = AgentId("Agent").with_root(tmp_path)
    todos = FileTodos()

    todos.write(agent_id, "- [ ] write a test")

    assert todos.read(agent_id) == "- [ ] write a test"
