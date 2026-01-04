from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest
from textual.geometry import Offset, Size

from simple_agent.application.agent_id import AgentId
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.smart_input import SmartInput
from simple_agent.infrastructure.textual.smart_input.autocomplete import (
    CompletionResult,
    CursorAndLine,
    SuggestionList,
    Cursor,
    FileReferences
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import TriggeredSuggestionProvider, CompositeSuggestionProvider
from simple_agent.infrastructure.textual.smart_input.autocomplete.file_search import (
    AtSymbolTrigger, FileSearchProvider
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.popup import AutocompletePopup
from simple_agent.infrastructure.textual.smart_input.autocomplete.popup import (
    CompletionSeed,
    PopupLayout,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.slash_commands import (
    SlashAtStartOfLineTrigger, SlashCommandProvider
)
from simple_agent.infrastructure.textual.textual_app import TextualApp


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
    provider = CompositeSuggestionProvider([
        TriggeredSuggestionProvider(
            trigger=SlashAtStartOfLineTrigger(),
            provider=SlashCommandProvider(registry)
        )
    ])
    textarea = SmartInput(provider=provider)

    # Mount to trigger popup creation
    app = TextualApp(StubUserInput(), AgentId("Agent"))
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.mount(textarea)

        # Check that the provider is present on the SmartInput
        assert textarea.provider == provider


def test_triggered_suggestion_provider_requires_trigger_and_provider():
    # Helper to satisfy Protocol types without functionality
    class DummyTrigger:
        def is_triggered(self, _): return False

    class DummyProvider:
        async def suggest(self, _): return SuggestionList([])

    trigger = DummyTrigger()
    provider = DummyProvider()

    # Valid construction
    autocomplete = TriggeredSuggestionProvider(trigger=trigger, provider=provider)
    assert autocomplete.trigger is trigger
    assert autocomplete.provider is provider

    # Invalid constructions
    with pytest.raises(ValueError, match="Trigger cannot be None"):
        TriggeredSuggestionProvider(trigger=None, provider=provider)

    with pytest.raises(ValueError, match="Provider cannot be None"):
        TriggeredSuggestionProvider(trigger=trigger, provider=None)


@pytest.mark.asyncio
async def test_triggered_suggestion_provider_check_logic():
    class MockTrigger:
        def __init__(self, should_trigger): self.triggered = should_trigger
        def is_triggered(self, _): return self.triggered

    class MockProvider:
        async def suggest(self, _): return SuggestionList([SimpleSuggestion("s1")])

    cursor = CursorAndLine(Cursor(0,0), "")

    # triggered
    autocomplete = TriggeredSuggestionProvider(MockTrigger(True), MockProvider())
    suggestion_list = await autocomplete.suggest(cursor)
    assert isinstance(suggestion_list, SuggestionList)
    assert len(suggestion_list.suggestions) == 1
    assert suggestion_list.suggestions[0].display_text == "s1"

    # not triggered
    autocomplete = TriggeredSuggestionProvider(MockTrigger(False), MockProvider())
    suggestion_list = await autocomplete.suggest(cursor)
    assert isinstance(suggestion_list, SuggestionList)
    assert len(suggestion_list.suggestions) == 0


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
    # The prefix "ab" means the word started 2 chars ago
    seed = CompletionSeed(cursor_offset, "ab")

    # We need a dummy suggestion list
    suggestions = SuggestionList([SimpleSuggestion("abc")])

    layout = PopupLayout.calculate(suggestions, seed, screen_size)

    assert layout.offset.y == 11
    # cursor_offset.x (10) - width(2) = 8.
    # The layout shifts left by 2 to account for padding/styling, so 8 - 2 = 6.
    assert layout.offset.x == 6


def test_autocomplete_position_uses_above_when_no_room_below():
    screen_size = Size(80, 10)
    cursor_offset = Offset(10, 8)
    seed = CompletionSeed(cursor_offset, "ab")

    suggestions = SuggestionList([SimpleSuggestion("abc")]) # 1 item = height 1

    # Let's make it taller to force it above
    suggestions = SuggestionList([SimpleSuggestion("abc") for _ in range(3)]) # height 3

    # below would be 8+1 = 9. 9+3 = 12 > 10. So it should go above.
    # above_y = 8 - 3 = 5.

    layout = PopupLayout.calculate(suggestions, seed, screen_size)

    assert layout.offset.y == 5

def test_calculate_autocomplete_position_edge_cases():
    screen_size = Size(80, 24)
    popup_size = Size(20, 5) # Note: PopupLayout calculates size from suggestions, but we can verify logic

    # We need to simulate suggestions that result in specific size
    # height 5 -> 5 suggestions
    # width 20 -> max line length 18
    long_text = "a" * 18
    suggestions = SuggestionList([SimpleSuggestion(long_text) for _ in range(5)])

    cursor_offset = Offset(10, 5)
    seed = CompletionSeed(cursor_offset, "ab") # width 2
    layout = PopupLayout.calculate(suggestions, seed, screen_size)

    assert layout.offset.y == 6
    # 10 - 2 (width) - 2 (offset) = 6
    assert layout.offset.x == 6

    # Test bottom edge
    cursor_offset = Offset(10, 20)
    seed = CompletionSeed(cursor_offset, "ab")
    layout = PopupLayout.calculate(suggestions, seed, screen_size)
    # below: 21 + 5 = 26 > 24. above: 20 - 5 = 15.
    assert layout.offset.y == 15

    # Test right edge
    cursor_offset = Offset(75, 5)
    seed = CompletionSeed(cursor_offset, "ab") # start at 73. width 20. 73+20 = 93 > 80.
    # max_x = 80 - 20 = 60.
    layout = PopupLayout.calculate(suggestions, seed, screen_size)
    # x = min(max(73, 0), 60) -> 60
    # Wait, existing logic was: anchor_x = cursor - 2.
    # Existing logic in PopupAnchor:
    # anchor_x = self.cursor_offset.x - 2
    # But self.cursor_offset was constructed as `cursor_screen_offset.x - delta`.
    # Let's re-verify the old logic.
    # Old logic:
    # anchor_x = max(0, cursor_screen_offset.x - delta)
    # Then placement used `anchor_x - 2`.

    # In my new logic:
    # anchor_x = max(0, seed.location.x - seed.width) -> 75 - 2 = 73
    # anchor_point = Offset(73, ...)
    # _calculate_placement:
    # anchor_x = anchor_point.x - 2 -> 71.
    # max_x = 80 - 20 = 60.
    # x = min(71, 60) = 60.
    assert layout.offset.x == 60

    # Test left edge
    cursor_offset = Offset(1, 5) # prefix 2 chars -> -1 -> 0
    seed = CompletionSeed(cursor_offset, "ab")
    layout = PopupLayout.calculate(suggestions, seed, screen_size)
    assert layout.offset.x == 0

    # Small screen
    small_screen = Size(80, 10)
    cursor_offset = Offset(10, 8)
    seed = CompletionSeed(cursor_offset, "ab")
    layout = PopupLayout.calculate(suggestions, seed, small_screen)
    # below: 9 + 5 = 14 > 10.
    # above: 8 - 5 = 3.
    assert layout.offset.y == 3

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

        # Create suggestions manually
        strings = [
            "/short - desc",
            "/looooooong - description"
        ]

        suggestions = [SimpleSuggestion(s) for s in strings]

        # Manually set state to simulate start() without async search
        # seed at 10,10, empty text (width 0) for simplicity
        seed = CompletionSeed(Offset(10, 10), "")

        popup.show(SuggestionList(suggestions), seed)

        await pilot.pause()

        assert popup.display is True
        # Verify width accommodates the long suggestion
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
        seed = CompletionSeed(Offset(0, 0), "")

        popup.show(SuggestionList(suggestions), seed)
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

                # Inject our custom provider
                provider = CompositeSuggestionProvider([
                    TriggeredSuggestionProvider(
                        trigger=AtSymbolTrigger(),
                        provider=FileSearchProvider(mock_searcher)
                    )
                ])
                yield SmartInput(provider=provider, id="user-input")

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
