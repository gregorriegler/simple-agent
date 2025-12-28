
import pytest
from pathlib import Path
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace
from simple_agent.application.agent_id import AgentId
from textual.widgets import Markdown

def test_refresh_todos_updates_content_from_file(tmp_path):
    agent_id = AgentId("test_agent")
    # Use the production logic to determine the filename
    filename = agent_id.todo_filename()
    todo_file = tmp_path / filename
    todo_file.write_text("Initial content", encoding="utf-8")

    # Override todo_filename to return the absolute path to our temp file
    # This allows us to use tmp_path without changing the process working directory
    agent_id.todo_filename = lambda: str(todo_file)

    # Pass a dummy callback as it is required by __init__ but not used in this test
    workspace = AgentWorkspace(
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id",
        on_refresh_todos=lambda: None
    )

    assert workspace.todo_view.content == "Initial content"

    todo_file.write_text("Updated content", encoding="utf-8")
    workspace.refresh_todos()

    assert workspace.todo_view.content == "Updated content"
    assert workspace.todo_view.styles.display != "none"

    todo_file.write_text("", encoding="utf-8")
    workspace.refresh_todos()
    assert workspace.todo_view.content == ""
    assert workspace.todo_view.styles.display == "none"

def test_tool_log_receives_provided_callback():
    agent_id = AgentId("test_agent")
    # Define a specific callback to verify it is passed correctly
    def my_callback(): pass

    workspace = AgentWorkspace(
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id",
        on_refresh_todos=my_callback
    )

    assert workspace.tool_log.on_refresh_todos == my_callback
