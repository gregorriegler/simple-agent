import pytest
from textual.widgets import TabbedContent, TextArea, Static, Markdown
from textual.containers import VerticalScroll

from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.textual.textual_app import (
    TextualApp,
    SubmittableTextArea
)
from simple_agent.application.events import (
    SessionInterruptedEvent,
    SessionStartedEvent,
    SessionEndedEvent,
    ErrorEvent,
    SessionClearedEvent,
    UserPromptedEvent,
    AssistantSaidEvent,
    ToolCalledEvent,
    ToolResultEvent,
    ToolCancelledEvent,
    UserPromptRequestedEvent,
    AssistantRespondedEvent,
    AgentStartedEvent
)
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from unittest.mock import MagicMock, patch

class FakeUserInput:
    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def submit_input(self, content: str) -> None:
        return None

    def close(self) -> None:
        return None


@pytest.fixture
def app():
    return TextualApp(FakeUserInput(), AgentId("Agent"))


@pytest.mark.asyncio
async def test_switch_tabs_cycles_between_root_and_subagent(app: TextualApp):
    root_agent = AgentId("Agent")
    subagent = AgentId("Agent/Sub")

    async with app.run_test() as pilot:
        await pilot.pause()

        app.add_subagent_tab(subagent, "Sub")
        await pilot.pause()

        tabs = app.query_one("#tabs", TabbedContent)
        assert tabs.active == app.panel_ids_for(subagent)[0]

        app.action_next_tab()
        assert tabs.active == app.panel_ids_for(root_agent)[0]

        app.action_previous_tab()
        assert tabs.active == app.panel_ids_for(subagent)[0]


@pytest.mark.asyncio
async def test_write_tool_result_renders_diff_as_static(app: TextualApp):
    agent_id = AgentId("Agent")
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    call_id = "call-1"

    async with app.run_test() as pilot:
        await pilot.pause()

        app.write_tool_call(tool_results_id, call_id, "Tool Call\nInput: example")
        result = SingleToolResult(message="@@ -1 +1 @@\n-test\n+passed", display_language="diff")
        app.write_tool_result(tool_results_id, call_id, result)
        await pilot.pause()

        collapsible = app._tool_result_collapsibles[tool_results_id][-1]
        assert collapsible.query_one(Static)


@pytest.mark.asyncio
async def test_write_tool_cancelled_marks_call_as_cancelled(app: TextualApp):
    agent_id = AgentId("Agent")
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    call_id = "call-1"

    async with app.run_test() as pilot:
        await pilot.pause()

        app.write_tool_call(tool_results_id, call_id, "Tool Call\nInput: example")
        app.write_tool_cancelled(tool_results_id, call_id)
        await pilot.pause()

        collapsible = app._tool_result_collapsibles[tool_results_id][-1]
        text_area = collapsible.query_one(TextArea)
        assert text_area.text == "Cancelled"
        assert collapsible.title.endswith("(Cancelled)")


@pytest.mark.asyncio
async def test_write_tool_call_suppresses_write_todos(app: TextualApp):
    agent_id = AgentId("Agent")
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    call_id = "call-1"

    async with app.run_test() as pilot:
        await pilot.pause()

        app.write_tool_call(tool_results_id, call_id, "write-todos\nInput: example")
        assert call_id not in app._pending_tool_calls[tool_results_id]
        assert call_id in app._suppressed_tool_calls

        result = SingleToolResult(message="Done")
        app.write_tool_result(tool_results_id, call_id, result)
        assert call_id not in app._suppressed_tool_calls

@pytest.mark.asyncio
async def test_textual_app_lifecycle(app: TextualApp):
    async with app.run_test() as pilot:
        # Test action_quit
        with patch.object(app, "exit") as mock_exit:
            app.action_quit()
            mock_exit.assert_called_once()

        # Test shutdown
        with patch.object(app, "exit") as mock_exit:
            # We need to mock is_running=True ideally, but it should be true in test
            app.shutdown()
            mock_exit.assert_called_once()

@pytest.mark.asyncio
async def test_textual_app_write_message_error(app: TextualApp):
    async with app.run_test() as pilot:
        agent_id = AgentId("Agent")
        _, log_id, _ = app.panel_ids_for(agent_id)

        # Test write_message with valid log_id
        app.write_message(log_id, "Hello")
        await pilot.pause()
        scroll = app.query_one(f"#{log_id}-scroll", VerticalScroll).query_one(Markdown)
        assert scroll is not None

        # Test write_message with invalid log_id (should not raise)
        app.write_message("invalid-id", "Hello")

@pytest.mark.asyncio
async def test_textual_app_write_tool_result_suppressed(app: TextualApp):
    async with app.run_test() as pilot:
        agent_id = AgentId("Agent")
        _, _, tool_results_id = app.panel_ids_for(agent_id)
        call_id = "call-suppressed"

        # Simulate suppressed call (write-todos)
        app.write_tool_call(tool_results_id, call_id, "write-todos")
        assert call_id in app._suppressed_tool_calls

        # Write result, should be ignored (return early)
        result = SingleToolResult(message="Done")
        app.write_tool_result(tool_results_id, call_id, result)

        # Check that no result was rendered
        # suppressed calls are removed from suppressed list after result? No, in _pop_pending_tool_call
        assert call_id not in app._suppressed_tool_calls

@pytest.mark.asyncio
async def test_textual_app_write_tool_result_no_pending(app: TextualApp):
    async with app.run_test() as pilot:
        agent_id = AgentId("Agent")
        _, _, tool_results_id = app.panel_ids_for(agent_id)

        # Write result with no call
        result = SingleToolResult(message="Done")
        app.write_tool_result(tool_results_id, "unknown-call", result)
        # Should just log warning and not crash

@pytest.mark.asyncio
async def test_textual_app_clear_panels(app: TextualApp):
    async with app.run_test() as pilot:
        agent_id = AgentId("Agent")
        _, log_id, _ = app.panel_ids_for(agent_id)

        # Add content
        app.write_message(log_id, "Message")

        # Clear
        app.clear_agent_panels(log_id)
        await pilot.pause()

        # Verify cleared
        scroll = app.query_one(f"#{log_id}-scroll")
        assert len(scroll.children) == 0

@pytest.mark.asyncio
async def test_textual_app_events(app: TextualApp):
    async with app.run_test() as pilot:
        agent_id = AgentId("Agent")
        _, log_id, _ = app.panel_ids_for(agent_id)

        # SessionStartedEvent
        app.on_domain_event_message(DomainEventMessage(SessionStartedEvent(agent_id, is_continuation=False)))
        await pilot.pause()
        # Verify message
        # We can't easily check text content without querying specific widgets, assuming write_message works.

        # SessionInterruptedEvent
        app.on_domain_event_message(DomainEventMessage(SessionInterruptedEvent(agent_id)))
        await pilot.pause()

        # ErrorEvent
        app.on_domain_event_message(DomainEventMessage(ErrorEvent(agent_id, "Something wrong")))
        await pilot.pause()

        # SessionClearedEvent
        app.on_domain_event_message(DomainEventMessage(SessionClearedEvent(agent_id)))
        await pilot.pause()
        scroll = app.query_one(f"#{log_id}-scroll")
        assert len(scroll.children) == 0

@pytest.mark.asyncio
async def test_textual_app_submit_with_file_references(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SubmittableTextArea)
        text_area.text = "check this file"
        # Manually add reference
        text_area._referenced_files.add("test_file.txt")
        text_area.insert(" [📦test_file.txt]")

        # Mock Path
        with patch("simple_agent.infrastructure.textual.textual_app.Path") as mock_path:
            mock_path_obj = MagicMock()
            mock_path.return_value = mock_path_obj
            mock_path_obj.exists.return_value = True
            mock_path_obj.is_file.return_value = True
            mock_path_obj.read_text.return_value = "file content"

            # Mock submit_input
            mock_submit = MagicMock()
            app.user_input = MagicMock()
            app.user_input.submit_input = mock_submit

            app.action_submit_input()

            mock_submit.assert_called_once()
            call_arg = mock_submit.call_args[0][0]
            assert "check this file" in call_arg
            assert '<file_context path="test_file.txt">' in call_arg
            assert "file content" in call_arg
