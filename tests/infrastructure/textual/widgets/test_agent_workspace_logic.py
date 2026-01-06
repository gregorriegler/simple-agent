
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace
from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_results import SingleToolResult

def test_refresh_todos_updates_content_from_file(tmp_path):
    agent_id = AgentId("test_agent", root=tmp_path)
    # todo_filename returns an absolute path using tmp_path now
    todo_file = agent_id.todo_filename()
    todo_file.write_text("Initial content", encoding="utf-8")

    workspace = AgentWorkspace(
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id"
    )

    assert workspace.todo_view.content == "Initial content"

    todo_file.write_text("Updated content", encoding="utf-8")
    workspace.refresh_todos()

    assert workspace.todo_view.content == "Updated content"
    assert workspace.todo_view.styles.display != "none"

def test_refresh_todos_hides_view_when_empty(tmp_path):
    agent_id = AgentId("test_agent", root=tmp_path)
    todo_file = agent_id.todo_filename()
    todo_file.write_text("Initial content", encoding="utf-8")

    workspace = AgentWorkspace(
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id"
    )

    todo_file.write_text("", encoding="utf-8")
    workspace.refresh_todos()

    assert workspace.todo_view.content == ""
    assert workspace.todo_view.styles.display == "none"

def test_on_tool_result_triggers_todo_refresh(tmp_path):
    agent_id = AgentId("test_agent", root=tmp_path)
    todo_file = agent_id.todo_filename()
    todo_file.write_text("Initial", encoding="utf-8")

    workspace = AgentWorkspace(
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id"
    )

    # Simulate tool updating the file
    todo_file.write_text("Updated", encoding="utf-8")

    # Call on_tool_result
    result = SingleToolResult(message="Done")
    workspace.on_tool_result("call-1", result)

    assert workspace.todo_view.content == "Updated"

def test_on_tool_cancelled_triggers_todo_refresh(tmp_path):
    agent_id = AgentId("test_agent", root=tmp_path)
    todo_file = agent_id.todo_filename()
    todo_file.write_text("Initial", encoding="utf-8")

    workspace = AgentWorkspace(
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id"
    )

    # Simulate file change (unlikely on cancelled but verifies refresh happened)
    todo_file.write_text("Updated", encoding="utf-8")

    workspace.on_tool_cancelled("call-1")

    assert workspace.todo_view.content == "Updated"
