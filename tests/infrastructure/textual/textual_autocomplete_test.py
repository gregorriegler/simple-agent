import pytest
from textual.geometry import Offset, Size
from dataclasses import dataclass
from unittest.mock import MagicMock, AsyncMock

from simple_agent.application.slash_command_registry import SlashCommandRegistry, SlashCommand
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.widgets.smart_input import SmartInput
from simple_agent.infrastructure.textual.widgets.autocomplete_popup import (
    calculate_autocomplete_position,
    AutocompletePopup,
)
from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.textual.autocompletion import (
    AutocompleteRequest,
    SlashCommandAutocompleter,
    CompletionResult,
    SlashCommandSuggestion,
    FileSuggestion
)

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
    registry = SlashCommandRegistry()
    autocompleter = SlashCommandAutocompleter(registry)
    textarea = SmartInput(autocompleters=[autocompleter])
    
    assert any(isinstance(s, SlashCommandAutocompleter) for s in textarea._initial_autocompleters)


def test_get_autocomplete_suggestions_for_slash():
    registry = SlashCommandRegistry()
    
    suggestions = registry.get_matching_commands("/")
    
    assert len(suggestions) == 2
    assert any(cmd.name == "/clear" for cmd in suggestions)
    assert any(cmd.name == "/model" for cmd in suggestions)


def test_get_autocomplete_suggestions_for_partial():
    registry = SlashCommandRegistry()
    
    suggestions = registry.get_matching_commands("/m")
    
    assert len(suggestions) == 1
    assert suggestions[0].name == "/model"


def test_no_suggestions_for_regular_text():
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

    cursor_offset = Offset(10, 5)
    pos = calculate_autocomplete_position(cursor_offset, screen_size, popup_height, popup_width)
    assert pos.y == 6
    assert pos.x == 8

    cursor_offset = Offset(10, 20)
    pos = calculate_autocomplete_position(cursor_offset, screen_size, popup_height, popup_width)
    assert pos.y == 15

    cursor_offset = Offset(75, 5)
    pos = calculate_autocomplete_position(cursor_offset, screen_size, popup_height, popup_width)
    assert pos.x == 60

    cursor_offset = Offset(1, 5)
    pos = calculate_autocomplete_position(cursor_offset, screen_size, popup_height, popup_width)
    assert pos.x == 0

    small_screen = Size(80, 10)
    cursor_offset = Offset(10, 8)
    pos = calculate_autocomplete_position(cursor_offset, small_screen, popup_height, popup_width)
    assert pos.y == 3

@pytest.mark.asyncio
async def test_submit_hides_autocomplete_popup():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        popup = app.query_one("#autocomplete-popup")

        text_area.focus()
        await pilot.press("/")
        await pilot.press("c")
        await pilot.pause()

        assert popup.display is True

        await pilot.press("enter")
        await pilot.pause()

        assert not popup.display


@pytest.mark.asyncio
async def test_autocomplete_popup_keeps_initial_x_position():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        popup = app.query_one("#autocomplete-popup")
        text_area.focus()

        # Type to show popup
        await pilot.press("/")
        await pilot.press("c")
        await pilot.pause()

        assert popup.display
        initial_x = popup.absolute_offset.x

        # Continue typing
        await pilot.press("l")
        await pilot.press("e")
        await pilot.pause()

        assert popup.absolute_offset.x == initial_x


@pytest.mark.asyncio
async def test_enter_key_selects_autocomplete_when_visible():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        text_area.focus()
        
        await pilot.press("/")
        await pilot.press("c")
        await pilot.pause()
        
        assert text_area.popup.display is True
        
        await pilot.press("enter")
        await pilot.pause()
        
        assert text_area.text.startswith("/clear")
        assert len(user_input.inputs) == 0
        assert text_area.popup.display is False


@pytest.mark.asyncio
async def test_enter_key_submits_when_autocomplete_not_visible():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        text_area.focus()
        
        # Type "hello"
        for char in "hello":
            await pilot.press(char)
        await pilot.pause()

        if text_area.popup:
            assert text_area.popup.display is False
        
        await pilot.press("enter")
        await pilot.pause()
        
        assert len(user_input.inputs) == 1
        assert user_input.inputs[0] == "hello"

@pytest.mark.asyncio
async def test_autocomplete_popup_rendering(app: TextualApp):
    async with app.run_test() as pilot:
        popup = app.query_one(AutocompletePopup)
        screen_size = Size(80, 24)

        # Test rendering by injecting a Mock autocompleter that returns real Suggestions
        mock_completer = MagicMock()
        mock_completer.check.return_value = AutocompleteRequest("q", 0, "q")

        suggestion1 = SlashCommandSuggestion(SlashCommand("/short", "desc"))
        suggestion2 = SlashCommandSuggestion(SlashCommand("/looooooong", "description"))

        mock_completer.get_suggestions = AsyncMock(return_value=[suggestion1, suggestion2])

        popup.autocompleters = [mock_completer]

        # Call public check method
        popup.check(0, 1, "q", Offset(10, 10), screen_size)
        await pilot.pause()

        assert popup.display is True
        # Verify width accommodates the long suggestion
        # "/looooooong - description" length is roughly 11 + 3 + 11 = 25
        assert popup.styles.width.value > 20

        # Check content
        assert "/short" in str(popup.render())

@pytest.mark.asyncio
async def test_autocomplete_popup_hide(app: TextualApp):
    async with app.run_test() as pilot:
        popup = app.query_one(AutocompletePopup)
        # Force display via public check
        mock_completer = MagicMock()
        mock_completer.check.return_value = AutocompleteRequest("x", 0, "x")
        mock_completer.get_suggestions = AsyncMock(return_value=[SlashCommandSuggestion(SlashCommand("/a", "b"))])
        popup.autocompleters = [mock_completer]

        popup.check(0, 1, "x", Offset(0, 0), Size(80, 24))
        await pilot.pause()

        assert popup.display is True

        popup.hide()
        assert popup.display is False

@pytest.mark.asyncio
async def test_submittable_text_area_slash_commands(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SmartInput)
        popup = app.query_one(AutocompletePopup)

        text_area.focus()
        await pilot.press("/")
        await pilot.pause()

        assert text_area.popup.display is True
        assert popup.display is True

        # Type "c" "l" to filter
        await pilot.press("c")
        await pilot.press("l")
        await pilot.pause()

        # We assume /clear is the first suggestion or we select it.
        # Default selection index is 0.

        # Press Enter to select
        await pilot.press("enter")
        await pilot.pause()

        assert text_area.text.startswith("/clear")
        assert text_area.popup.display is False
        assert popup.display is False

@pytest.mark.asyncio
async def test_submittable_text_area_file_search(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SmartInput)
        text_area.focus()

        mock_searcher = AsyncMock()
        mock_searcher.search.return_value = ["my_file.py", "other_file.txt"]

        text_area.file_searcher = mock_searcher

        await pilot.press("s")
        await pilot.press(" ")

        await pilot.press("@")
        await pilot.press("m")
        await pilot.press("y")

        await pilot.pause()

        assert text_area.popup.display is True

        # Verify content via Textual's render if needed, or just behavior
        # Navigating down then up
        await pilot.press("down")
        await pilot.press("up")

        await pilot.press("enter")
        await pilot.pause()

        assert "[📦my_file.py]" in text_area.text
        assert "s " in text_area.text
        assert text_area.popup.display is False

@pytest.mark.asyncio
async def test_submittable_text_area_keyboard_interactions(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SmartInput)
        text_area.focus()

        # Trigger popup
        await pilot.press("/")
        await pilot.pause()

        assert text_area.popup.display is True

        # Test Escape
        await pilot.press("escape")
        await pilot.pause()
        assert text_area.popup.display is False

        # Re-open
        await pilot.press("backspace") # delete /
        await pilot.press("/")
        await pilot.pause()
        assert text_area.popup.display is True

        # Test Tab
        await pilot.press("tab")
        await pilot.pause()

        assert text_area.popup.display is False
        # Should have selected the first one (likely /clear or /model, sorted alphabetically?)
        # Just check it started with /
        assert text_area.text.startswith("/")
        assert len(text_area.text) > 1

@pytest.mark.asyncio
async def test_submittable_text_area_ctrl_enter(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SmartInput)
        text_area.focus()
        text_area.text = "line1"
        text_area.move_cursor((0, 5))

        await pilot.press("ctrl+enter")
        await pilot.pause()

        assert text_area.text == "line1\n"
