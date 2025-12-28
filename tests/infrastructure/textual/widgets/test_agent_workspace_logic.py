
import pytest
from unittest.mock import MagicMock
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace
from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog
from simple_agent.infrastructure.textual.widgets.todo_view import TodoView
from simple_agent.infrastructure.textual.resizable_container import ResizableVertical

class TestAgentWorkspace:
    def test_refresh_todos_delegates_to_todo_view(self):
        # Arrange
        agent_id = AgentId("test_agent")
        mock_callback = MagicMock()
        workspace = AgentWorkspace(
            agent_id=agent_id,
            log_id="log-id",
            tool_results_id="tool-id",
            on_refresh_todos=mock_callback
        )

        # Mock internal widgets
        workspace.todo_view = MagicMock(spec=TodoView)
        workspace.todo_view.has_content = True
        workspace.left_panel = MagicMock(spec=ResizableVertical)

        # Act
        workspace.refresh_todos()

        # Assert
        workspace.todo_view.refresh_content.assert_called_once()
        workspace.left_panel.set_bottom_visibility.assert_called_with(True)

    def test_tool_log_receives_provided_callback(self):
        # Arrange
        agent_id = AgentId("test_agent")
        mock_callback = MagicMock()
        workspace = AgentWorkspace(
            agent_id=agent_id,
            log_id="log-id",
            tool_results_id="tool-id",
            on_refresh_todos=mock_callback
        )

        # Assert
        # Verify that ToolLog was initialized with the passed callback
        # ToolLog stores it as on_refresh_todos
        assert workspace.tool_log.on_refresh_todos == mock_callback
