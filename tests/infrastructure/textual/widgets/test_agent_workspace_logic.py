
import pytest
from pathlib import Path
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace
from simple_agent.application.agent_id import AgentId
from textual.widgets import Markdown

def test_refresh_todos_updates_content_from_file(tmp_path):
    agent_id = AgentId("test_agent")
    filename = agent_id.todo_filename()
    todo_file = tmp_path / filename
    todo_file.write_text("Initial content", encoding="utf-8")

    agent_id.todo_filename = lambda: str(todo_file)

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

def test_refresh_todos_hides_view_when_empty(tmp_path):
    agent_id = AgentId("test_agent")
    filename = agent_id.todo_filename()
    todo_file = tmp_path / filename
    todo_file.write_text("Initial content", encoding="utf-8")

    agent_id.todo_filename = lambda: str(todo_file)

    workspace = AgentWorkspace(
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id",
        on_refresh_todos=lambda: None
    )

    todo_file.write_text("", encoding="utf-8")
    workspace.refresh_todos()

    assert workspace.todo_view.content == ""
    assert workspace.todo_view.styles.display == "none"

def test_tool_log_receives_provided_callback():
    agent_id = AgentId("test_agent")
    def my_callback(): pass

    workspace = AgentWorkspace(
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id",
        on_refresh_todos=my_callback
    )

    assert workspace.tool_log.on_refresh_todos == my_callback
