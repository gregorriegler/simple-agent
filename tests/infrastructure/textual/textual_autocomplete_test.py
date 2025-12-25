import pytest
from textual.geometry import Offset, Size
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, AsyncMock

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_app import (
    SubmittableTextArea,
    calculate_autocomplete_position,
    AutocompletePopup,
)
from simple_agent.application.agent_id import AgentId

class StubUserInput:
    def __init__(self) -> None:
        self.inputs = []

    def submit_input(self, content: str) -> None:
        self.inputs.append(content)

    def close(self) -> None:
        pass

    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

@pytest.fixture
def app():
    return TextualApp(StubUserInput(), AgentId("Agent"))


def test_slash_command_registry_available_in_textarea():
    """Test that we can attach a registry to the textarea."""
    registry = SlashCommandRegistry()
    textarea = SubmittableTextArea()
    
    # For now, just verify we can set it
    textarea.slash_command_registry = registry
    assert textarea.slash_command_registry is not None


def test_get_autocomplete_suggestions_for_slash():
    """Test getting suggestions when user types '/'."""
    registry = SlashCommandRegistry()
    
    suggestions = registry.get_matching_commands("/")
    
    assert len(suggestions) == 2
    assert any(cmd.name == "/clear" for cmd in suggestions)
    assert any(cmd.name == "/model" for cmd in suggestions)


def test_get_autocomplete_suggestions_for_partial():
    """Test getting suggestions when user types '/m'."""
    registry = SlashCommandRegistry()
    
    suggestions = registry.get_matching_commands("/m")
    
    assert len(suggestions) == 1
    assert suggestions[0].name == "/model"


def test_no_suggestions_for_regular_text():
    """Test that regular text doesn't trigger suggestions."""
    registry = SlashCommandRegistry()
    
    suggestions = registry.get_matching_commands("hello")
    
    assert len(suggestions) == 0


def test_autocomplete_position_prefers_below_cursor():
    screen_size = Size(80, 24)
    cursor_offset = Offset(10, 10)

    position = calculate_autocomplete_position(
        cursor_offset=cursor_offset,
        screen_size=screen_size,
        popup_height=3,
        popup_width=12,
    )

    assert position.y == 11
    assert position.x == 8


def test_autocomplete_position_uses_above_when_no_room_below():
    screen_size = Size(80, 10)
    cursor_offset = Offset(10, 8)

    position = calculate_autocomplete_position(
        cursor_offset=cursor_offset,
        screen_size=screen_size,
        popup_height=3,
        popup_width=12,
    )

    assert position.y == 5

def test_calculate_autocomplete_position_edge_cases():
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
async def test_submit_hides_autocomplete_popup():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.query_one("#user-input", SubmittableTextArea)
        popup = app.query_one("#autocomplete-popup")

        text_area.text = "/clear"
        text_area._show_autocomplete(text_area.text)
        assert popup.display

        app.action_submit_input()
        await pilot.pause()

        assert not popup.display


@pytest.mark.asyncio
async def test_autocomplete_popup_keeps_initial_x_position():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.query_one("#user-input", SubmittableTextArea)
        popup = app.query_one("#autocomplete-popup")

        text_area.text = "/c"
        text_area._show_autocomplete(text_area.text)
        await pilot.pause()
        initial_x = popup.absolute_offset.x

        text_area.text = "/clear"
        text_area._show_autocomplete(text_area.text)
        await pilot.pause()

        assert popup.absolute_offset.x == initial_x


@pytest.mark.asyncio
async def test_enter_key_selects_autocomplete_when_visible():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SubmittableTextArea)
        
        # Trigger autocomplete
        text_area.text = "/c"
        # Manually trigger the check/show because typing simulation might be async/complex
        text_area._active_trigger = "/"
        text_area._show_autocomplete("/c")
        
        assert text_area._autocomplete_visible is True
        
        # Press Enter
        await pilot.press("enter")
        
        # Expectation:
        # 1. Autocomplete should complete the text to "/clear "
        # 2. Input should NOT be submitted yet
        # 3. Autocomplete should be hidden
        
        assert text_area.text.startswith("/clear")
        assert len(user_input.inputs) == 0
        assert text_area._autocomplete_visible is False


@pytest.mark.asyncio
async def test_enter_key_submits_when_autocomplete_not_visible():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SubmittableTextArea)
        
        # Type something
        text_area.text = "hello"
        assert text_area._autocomplete_visible is False
        
        # Press Enter
        await pilot.press("enter")
        
        # Expectation:
        # 1. Input should be submitted
        
        assert len(user_input.inputs) == 1
        assert user_input.inputs[0] == "hello"

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
        # Reduced pause
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
