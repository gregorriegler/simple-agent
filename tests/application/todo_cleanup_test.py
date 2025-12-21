from simple_agent.application.agent_id import AgentId
from simple_agent.application.todo_cleanup import NoOpTodoCleanup


def test_noop_todo_cleanup_methods_return_none():
    cleanup = NoOpTodoCleanup()

    assert cleanup.cleanup_all_todos() is None
    assert cleanup.cleanup_todos_for_agent(AgentId("Agent")) is None
