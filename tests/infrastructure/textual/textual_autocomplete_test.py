import pytest
from textual.geometry import Offset, Size
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.widgets.smart_input import SmartInput
from simple_agent.infrastructure.textual.widgets.autocomplete_popup import (
    calculate_autocomplete_position,
    AutocompletePopup,
)
from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.textual.autocompletion import AutocompleteRequest, SlashCommandAutocompleter, CompletionResult

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

@dataclass
class TestSuggestion:
    display_text: str
    result_text: str = ""

    def to_completion_result(self) -> CompletionResult:
        return CompletionResult(text=self.result_text)

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
        await pilot.pause()
        text_area = app.query_one("#user-input", SmartInput)
        popup = app.query_one("#autocomplete-popup")

        text_area.text = "/clear"
        text_area.move_cursor((0, len("/clear")))

        text_area._trigger_autocomplete_check()
        await pilot.pause()

        assert text_area.popup._active_autocompleter is not None

        app.action_submit_input()
        await pilot.pause()

        assert not popup.display


@pytest.mark.asyncio
async def test_autocomplete_popup_keeps_initial_x_position():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.query_one("#user-input", SmartInput)
        popup = app.query_one("#autocomplete-popup")

        text_area.text = "/c"
        text_area.move_cursor((0, len("/c")))
        text_area._trigger_autocomplete_check()
        await pilot.pause()

        assert text_area.popup.display
        initial_x = popup.absolute_offset.x

        text_area.text = "/clear"
        text_area.move_cursor((0, len("/clear")))
        text_area._trigger_autocomplete_check()
        await pilot.pause()

        assert popup.absolute_offset.x == initial_x


@pytest.mark.asyncio
async def test_enter_key_selects_autocomplete_when_visible():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        
        text_area.text = "/c"
        text_area.move_cursor((0, len("/c")))
        text_area._trigger_autocomplete_check()
        await pilot.pause()
        
        assert text_area.popup.display is True
        
        await pilot.press("enter")
        
        assert text_area.text.startswith("/clear")
        assert len(user_input.inputs) == 0
        assert text_area.popup.display is False


@pytest.mark.asyncio
async def test_enter_key_submits_when_autocomplete_not_visible():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        
        text_area.text = "hello"
        if text_area.popup:
            assert text_area.popup.display is False
        
        await pilot.press("enter")
        
        assert len(user_input.inputs) == 1
        assert user_input.inputs[0] == "hello"

@pytest.mark.asyncio
async def test_autocomplete_popup_show_suggestions(app: TextualApp):
    async with app.run_test() as pilot:
        popup = app.query_one(AutocompletePopup)
        screen_size = Size(80, 24)

        popup._show_suggestions([], Offset(0, 0), screen_size)
        assert popup.display is False

        suggestion1 = TestSuggestion(display_text="option1")
        suggestion2 = TestSuggestion(display_text="option2 long")

        lines = [suggestion1, suggestion2]

        cursor_offset = Offset(10, 10)
        popup._show_suggestions(lines, cursor_offset, screen_size)

        assert popup.display is True
        assert popup.styles.width is not None
        assert popup.styles.width.value == 14
        assert popup.styles.height.value == 2

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
        text_area = app.query_one(SmartInput)
        popup = app.query_one(AutocompletePopup)

        text_area.focus()
        await pilot.press("/")
        await pilot.pause()

        assert text_area.popup.display is True
        assert popup.display is True
        assert text_area.popup._active_request.trigger_char == "/"

        assert len(text_area.popup._current_suggestions) > 0

        await pilot.press("c")
        await pilot.press("l")
        await pilot.pause()

        text_area.popup._selected_index = 0
        result = text_area.popup._get_selection()
        text_area._apply_completion(result)

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

        text_area.insert("some text ")

        await pilot.press("@")
        await pilot.press("m")
        await pilot.press("y")

        await pilot.pause()

        assert text_area.popup.display is True
        assert text_area.popup._active_request.trigger_char == "@"
        assert len(text_area.popup._current_suggestions) > 0
        assert "my_file.py" in text_area.popup._current_suggestions[0].display_text

        await pilot.press("down")
        assert text_area.popup._selected_index == 1

        await pilot.press("up")
        assert text_area.popup._selected_index == 0

        await pilot.press("enter")

        assert "[📦my_file.py]" in text_area.text
        assert "some text" in text_area.text
        assert text_area.popup.display is False

@pytest.mark.asyncio
async def test_submittable_text_area_keyboard_interactions(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SmartInput)
        text_area.focus()

        strategy = SlashCommandAutocompleter(SlashCommandRegistry())
        request = AutocompleteRequest(query="/", start_index=0, trigger_char="/")
        text_area.popup._active_autocompleter = strategy
        text_area.popup._active_request = request

        suggestion = TestSuggestion(display_text="Display Text", result_text="/cmd ")

        text_area.popup._show_suggestions([suggestion], Offset(0,0), Size(80,24))
        assert text_area.popup.display is True

        await pilot.press("escape")
        assert text_area.popup.display is False

        text_area.popup._active_autocompleter = strategy
        text_area.popup._active_request = request
        text_area.popup._show_suggestions([suggestion], Offset(0,0), Size(80,24))

        await pilot.press("tab")
        await pilot.pause()

        assert text_area.popup.display is False
        assert text_area.text.startswith("/cmd")

@pytest.mark.asyncio
async def test_submittable_text_area_ctrl_enter(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SmartInput)
        text_area.focus()
        text_area.text = "line1"
        text_area.move_cursor((0, 5))

        await pilot.press("ctrl+enter")

        assert text_area.text == "line1\n"
