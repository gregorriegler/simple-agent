
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace
from simple_agent.application.agent_id import AgentId
from textual.widgets import Markdown

class TestAgentWorkspace:
    def test_refresh_todos_updates_content_from_file(self, tmp_path):
        agent_id = AgentId("test_agent")
        todo_file = tmp_path / "todos.md"
        todo_file.write_text("Initial content", encoding="utf-8")

        # Override todo_filename to return the absolute path to our temp file
        agent_id.todo_filename = lambda: str(todo_file)

        mock_callback = MagicMock()
        workspace = AgentWorkspace(
            agent_id=agent_id,
            log_id="log-id",
            tool_results_id="tool-id",
            on_refresh_todos=mock_callback
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

    def test_tool_log_receives_provided_callback(self):
        agent_id = AgentId("test_agent")
        mock_callback = MagicMock()
        workspace = AgentWorkspace(
            agent_id=agent_id,
            log_id="log-id",
            tool_results_id="tool-id",
            on_refresh_todos=mock_callback
        )

        assert workspace.tool_log.on_refresh_todos == mock_callback
