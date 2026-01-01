import pytest
import asyncio
from textual.geometry import Offset, Size
from dataclasses import dataclass
from unittest.mock import MagicMock, AsyncMock

from simple_agent.application.slash_command_registry import SlashCommandRegistry, SlashCommand
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.widgets.smart_input import SmartInput
from simple_agent.infrastructure.textual.autocomplete.popup import AutocompletePopup
from simple_agent.infrastructure.textual.autocomplete.geometry import (
    PopupAnchor,
    CaretScreenLocation
)
from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.textual.autocomplete import (
    CompletionResult,
    SlashCommandSuggestion,
    FileSuggestion,
    CursorAndLine,
    SuggestionList,
    Suggestion,
)
from simple_agent.infrastructure.textual.autocomplete.rules import AutocompleteRule
from simple_agent.infrastructure.textual.autocomplete.slash_commands import (
    SlashAtStartOfLineTrigger, SlashCommandProvider
)
from simple_agent.infrastructure.textual.autocomplete.file_search import (
    AtSymbolTrigger, FileSearchProvider
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


@pytest.mark.asyncio
async def test_slash_command_registry_available_in_textarea():
    registry = SlashCommandRegistry()
    rules = [
        AutocompleteRule(
            trigger=SlashAtStartOfLineTrigger(),
            provider=SlashCommandProvider(registry)
        )
    ]
    textarea = SmartInput(rules=rules)
    
    # Mount to trigger popup creation
    app = TextualApp(StubUserInput(), AgentId("Agent"))
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.mount(textarea)

        # Check that the rules are present on the SmartInput
        assert list(textarea.rules) == rules


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
    anchor = PopupAnchor(cursor_offset, screen_size)

    position = anchor.get_placement(Size(12, 3))

    assert position.y == 11
    assert position.x == 8


def test_autocomplete_position_uses_above_when_no_room_below():
    screen_size = Size(80, 10)
    cursor_offset = Offset(10, 8)
    anchor = PopupAnchor(cursor_offset, screen_size)

    position = anchor.get_placement(Size(12, 3))

    assert position.y == 5

def test_calculate_autocomplete_position_edge_cases():
    screen_size = Size(80, 24)
    popup_size = Size(20, 5)

    cursor_offset = Offset(10, 5)
    anchor = PopupAnchor(cursor_offset, screen_size)
    pos = anchor.get_placement(popup_size)
    assert pos.y == 6
    assert pos.x == 8

    cursor_offset = Offset(10, 20)
    anchor = PopupAnchor(cursor_offset, screen_size)
    pos = anchor.get_placement(popup_size)
    assert pos.y == 15

    cursor_offset = Offset(75, 5)
    anchor = PopupAnchor(cursor_offset, screen_size)
    pos = anchor.get_placement(popup_size)
    assert pos.x == 60

    cursor_offset = Offset(1, 5)
    anchor = PopupAnchor(cursor_offset, screen_size)
    pos = anchor.get_placement(popup_size)
    assert pos.x == 0

    small_screen = Size(80, 10)
    cursor_offset = Offset(10, 8)
    anchor = PopupAnchor(cursor_offset, small_screen)
    pos = anchor.get_placement(popup_size)
    assert pos.y == 3

@pytest.mark.asyncio
async def test_submit_hides_autocomplete_popup():
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)

        text_area.focus()
        await pilot.press("/")
        await pilot.press("c")
        await pilot.pause()

        popup = app.query_one(AutocompletePopup)
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
        text_area.focus()

        # Type to show popup
        await pilot.press("/")
        await pilot.press("c")
        await pilot.pause()

        popup = app.query_one(AutocompletePopup)
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

        # When closed, popup should be hidden
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

        assert text_area.popup.display is False
        
        await pilot.press("enter")
        await pilot.pause()
        
        assert len(user_input.inputs) == 1
        assert user_input.inputs[0] == "hello"

@dataclass
class SimpleSuggestion:
    display_text: str

    def to_completion_result(self) -> CompletionResult:
        return CompletionResult(text=self.display_text)

@pytest.mark.asyncio
async def test_autocomplete_popup_rendering(app: TextualApp):
    async with app.run_test() as pilot:
        popup = AutocompletePopup(id="autocomplete-popup")
        await app.mount(popup)
        screen_size = Size(80, 24)

        # Create suggestions manually
        strings = [
            "/short - desc",
            "/looooooong - description"
        ]

        suggestions = [SimpleSuggestion(s) for s in strings]
        # Calculate anchor manually (simulating what SmartInput does)
        cursor_offset = Offset(10, 10)
        anchor = PopupAnchor(cursor_offset, screen_size)

        # Manually set state to simulate start() without async search
        popup._show_suggestions(suggestions, anchor)

        await pilot.pause()

        assert popup.display is True
        # Verify width accommodates the long suggestion
        # "/looooooong - description" length is roughly 25
        assert popup.styles.width.value > 20

        # Check content
        assert "/short" in str(popup.render())

@pytest.mark.asyncio
async def test_autocomplete_popup_hide(app: TextualApp):
    async with app.run_test() as pilot:
        popup = AutocompletePopup(id="autocomplete-popup")
        await app.mount(popup)

        strings = ["/cmd - desc"]
        suggestions = [SimpleSuggestion(s) for s in strings]

        anchor = PopupAnchor(Offset(0, 0), Size(80, 24))

        popup._show_suggestions(suggestions, anchor)
        await pilot.pause()

        assert popup.display is True

        popup.close()
        assert popup.display is False

@pytest.mark.asyncio
async def test_submittable_text_area_slash_commands(app: TextualApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(SmartInput)

        text_area.focus()
        await pilot.press("/")
        await pilot.pause()

        popup = app.query_one(AutocompletePopup)
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

@pytest.mark.asyncio
async def test_submittable_text_area_file_search(app: TextualApp):
    # Mock searcher
    mock_searcher = AsyncMock()
    mock_searcher.search.return_value = ["my_file.py", "other_file.txt"]

    # Subclass TextualApp to inject dependencies
    class TestApp(TextualApp):
        def compose(self):
            from textual.containers import Vertical
            from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
            with Vertical():
                yield AgentTabs(self._root_agent_id, id="tabs")

                # Inject our custom rules
                rules = [AutocompleteRule(
                    trigger=AtSymbolTrigger(),
                    provider=FileSearchProvider(mock_searcher)
                )]
                yield SmartInput(rules=rules, id="user-input")

    test_app = TestApp(StubUserInput(), AgentId("Agent"))

    async with test_app.run_test() as pilot:
        text_area = test_app.query_one(SmartInput)
        text_area.focus()

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
        await pilot.pause() # Wait for async fetch

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
