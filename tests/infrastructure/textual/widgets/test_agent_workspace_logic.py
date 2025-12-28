
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace
from simple_agent.application.agent_id import AgentId
from textual.widgets import Markdown

class TestAgentWorkspace:
    def test_refresh_todos_updates_content_from_file(self, tmp_path):
        # Arrange
        agent_id = AgentId("test_agent")
        # Define the expected filename based on AgentId logic
        filename = agent_id.todo_filename()
        todo_file = tmp_path / filename
        todo_file.write_text("Initial content", encoding="utf-8")

        # Mock Path in TodoView to redirect to tmp_path
        # We need to mock it such that Path(filename) resolves to tmp_path / filename
        # But TodoView does `Path(self.agent_id.todo_filename())`
        # So we can just monkeypatch the specific file read?
        # Or easier: Mock `Path` in the module to return our tmp path.

        # Strategy: Monkeypatch `simple_agent.infrastructure.textual.widgets.todo_view.Path`
        # such that when initialized with the expected filename, it acts like our tmp file.
        # But Path is a class.

        # Simpler strategy: Since TodoView just does `Path(...)`, if we chdir to tmp_path, it works.
        # pytest's monkeypatch context manager can handle chdir safely.
        with pytest.MonkeyPatch.context() as m:
            m.chdir(tmp_path)

            # Initialize Workspace (uses real widgets)
            # We provide a mock callback just to satisfy the interface if needed,
            # though we want to test the default behavior if we were refactoring.
            # But currently `AgentWorkspace` requires `on_refresh_todos`.
            mock_callback = MagicMock()
            workspace = AgentWorkspace(
                agent_id=agent_id,
                log_id="log-id",
                tool_results_id="tool-id",
                on_refresh_todos=mock_callback
            )

            # Wait for mount? Tests using widgets directly without an App might behave differently.
            # However, `load_content` is called in `__init__`.
            # Check initial content
            assert workspace.todo_view.content == "Initial content"

            # Act: Update file and refresh
            todo_file.write_text("Updated content", encoding="utf-8")
            workspace.refresh_todos()

            # Assert
            assert workspace.todo_view.content == "Updated content"

            # Verify visibility toggle (requires peeking at styles or internal state)
            # If content is present, it should be visible.
            # ResizableVertical sets `display` style.
            # Note: without an App, styles might not be fully computed, but attributes should be set.
            # However, `set_bottom_visibility` toggles `self.bottom_widget.styles.display` and splitter.
            assert workspace.todo_view.styles.display != "none"

            # Test empty content hiding
            todo_file.write_text("", encoding="utf-8")
            workspace.refresh_todos()
            assert workspace.todo_view.content == ""
            # Verify it is hidden
            # set_bottom_visibility(False) sets display to "none"
            assert workspace.todo_view.styles.display == "none"

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
        # We access the real ToolLog instance
        assert workspace.tool_log.on_refresh_todos == mock_callback
