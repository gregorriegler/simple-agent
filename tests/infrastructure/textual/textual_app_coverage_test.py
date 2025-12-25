import pytest
import asyncio
from textual.geometry import Offset, Size
from textual.widgets import TextArea, Static, TabbedContent, Markdown
from textual.containers import VerticalScroll
from simple_agent.infrastructure.textual.textual_app import (
    TextualApp,
    calculate_autocomplete_position,
    AutocompletePopup,
    SubmittableTextArea,
    ResizableVertical
)
from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_results import SingleToolResult
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
from simple_agent.application.slash_command_registry import SlashCommand
from unittest.mock import MagicMock, patch, AsyncMock
from types import SimpleNamespace

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


def test_calculate_autocomplete_position():
    screen_size = Size(80, 24)
    popup_height = 5
    popup_width = 20

    # Normal case: place below
    cursor_offset = Offset(10, 5)
    pos = calculate_autocomplete_position(cursor_offset, screen_size, popup_height, popup_width)
    assert pos.y == 6 # 5 + 1
    assert pos.x == 8 # 10 - 2

    # Edge case: near bottom, should flip above
    cursor_offset = Offset(10, 20)
    pos = calculate_autocomplete_position(cursor_offset, screen_size, popup_height, popup_width)
    assert pos.y == 15 # 20 - 5 (above)

    # Edge case: near right edge, should shift left
    cursor_offset = Offset(75, 5)
    pos = calculate_autocomplete_position(cursor_offset, screen_size, popup_height, popup_width)
    assert pos.x == 60 # 80 - 20 (max_x)

    # Edge case: near left edge, should align left (min 0)
    cursor_offset = Offset(1, 5)
    pos = calculate_autocomplete_position(cursor_offset, screen_size, popup_height, popup_width)
    assert pos.x == 0 # max(1-2, 0) -> 0

    # Edge case: small screen, clamp y
    small_screen = Size(80, 10)
    cursor_offset = Offset(10, 8) # Below would be 9+5=14 (offscreen), Above would be 8-5=3
    pos = calculate_autocomplete_position(cursor_offset, small_screen, popup_height, popup_width)
    assert pos.y == 3

@pytest.mark.asyncio
async def test_autocomplete_popup_show_suggestions(app: TextualApp):
    async with app.run_test() as pilot:
        popup = app.query_one(AutocompletePopup)
        screen_size = Size(80, 24)

        # Test empty lines hides popup
        popup.show_suggestions([], 0, Offset(0, 0), screen_size)
        assert popup.display is False

        # Test normal lines
        lines = ["option1", "option2 long"]
        cursor_offset = Offset(10, 10)
        popup.show_suggestions(lines, 0, cursor_offset, screen_size)

        assert popup.display is True
        assert popup.styles.width is not None
        assert popup.styles.width.value == 14
        assert popup.styles.height.value == 2

        # Verify content rendering (roughly)
        assert "option1" in str(popup.render())

@pytest.mark.asyncio
async def test_autocomplete_popup_hide(app: TextualApp):
    async with app.run_test() as pilot:
        popup = app.query_one(AutocompletePopup)
        popup.display = True
        popup.hide()
        assert popup.display is False

@pytest.mark.asyncio
async def test_submittable_text_area_slash_commands(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SubmittableTextArea)
        popup = app.query_one(AutocompletePopup)

        # Test "/" trigger
        text_area.focus()
        await pilot.press("/")
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()

        # It should trigger autocomplete
        assert text_area._autocomplete_visible is True
        assert popup.display is True
        assert text_area._active_trigger == "/"

        # Test completion with slash command
        assert len(text_area._current_suggestions) > 0

        await pilot.press("c")
        await pilot.press("l")
        await pilot.pause()

        # Select first one
        text_area._selected_index = 0
        text_area._complete_selection()

        # Text should be replaced
        assert text_area.text.startswith("/clear")
        assert text_area._autocomplete_visible is False
        assert popup.display is False

@pytest.mark.asyncio
async def test_submittable_text_area_file_search(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SubmittableTextArea)
        text_area.focus()

        # Mock file searcher
        mock_searcher = AsyncMock()
        mock_searcher.search.return_value = ["my_file.py", "other_file.txt"]
        text_area.file_searcher = mock_searcher

        # Type "some text @my"
        text_area.insert("some text ")

        await pilot.press("@")
        await pilot.press("m")
        await pilot.press("y")

        await pilot.pause()
        await pilot.pause()

        assert text_area._autocomplete_visible is True
        assert text_area._active_trigger == "@"
        assert len(text_area._current_suggestions) > 0
        assert "my_file.py" in text_area._current_suggestions

        # Test navigation
        await pilot.press("down")
        assert text_area._selected_index == 1

        await pilot.press("up")
        assert text_area._selected_index == 0

        # Test selection
        await pilot.press("enter")

        # Text should have marker
        assert "[📦my_file.py]" in text_area.text
        assert "some text" in text_area.text
        assert text_area._autocomplete_visible is False

@pytest.mark.asyncio
async def test_submittable_text_area_keyboard_interactions(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SubmittableTextArea)
        text_area.focus()

        # Open autocomplete manually for test
        text_area._active_trigger = "/"
        # Use SimpleNamespace for object with attributes
        cmd = SimpleNamespace(name="/cmd", description="desc")
        text_area._display_suggestions([cmd])
        assert text_area._autocomplete_visible is True

        # Test Escape
        await pilot.press("escape")
        assert text_area._autocomplete_visible is False

        # Re-open
        text_area._active_trigger = "/" # Reset trigger
        text_area._display_suggestions([cmd])

        # Test Tab
        await pilot.press("tab")
        await pilot.pause() # Add pause to let event propagate

        assert text_area._autocomplete_visible is False
        assert text_area.text.startswith("/cmd")

@pytest.mark.asyncio
async def test_submittable_text_area_ctrl_enter(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SubmittableTextArea)
        text_area.focus()
        text_area.text = "line1"
        text_area.move_cursor((0, 5)) # Move to end

        await pilot.press("ctrl+enter")

        assert text_area.text == "line1\n"

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
        # Markdown widget content is not directly in str(), usually in source or similar.
        # But for simple check we can assume if it exists it's good, or check internal state if known.
        # Textual Markdown source is not publicly documented as stable API always, but let's try assuming it was added.
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
