from dataclasses import dataclass
from typing import cast
from unittest.mock import AsyncMock

import pytest
from textual.geometry import Offset, Size

from simple_agent.application.agent_id import AgentId
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.smart_input import SmartInput
from simple_agent.infrastructure.textual.smart_input.autocomplete import (
    CompletionResult,
    Cursor,
    CursorAndLine,
    SuggestionList,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    AutocompleteTrigger,
    CompositeSuggestionProvider,
    SuggestionProvider,
    TriggeredSuggestionProvider,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.file_search import (
    AtSymbolTrigger,
    FileSearchProvider,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.popup import (
    AutocompletePopup,
    CompletionSeed,
    PopupLayout,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.slash_commands import (
    SlashAtStartOfLineTrigger,
    SlashCommandArgumentProvider,
    SlashCommandArgumentTrigger,
    SlashCommandProvider,
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
def app(agent_task_manager):
    return TextualApp(StubUserInput(), AgentId("Agent"), agent_task_manager)


@pytest.mark.asyncio
async def test_slash_command_registry_available_in_textarea(agent_task_manager):
    registry = SlashCommandRegistry()
    provider = CompositeSuggestionProvider(
        [
            TriggeredSuggestionProvider(
                trigger=SlashAtStartOfLineTrigger(),
                provider=SlashCommandProvider(registry),
            )
        ]
    )
    textarea = SmartInput(provider=provider)

    # Mount to trigger popup creation
    app = TextualApp(StubUserInput(), AgentId("Agent"), agent_task_manager)
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.mount(textarea)

        # Check that the provider is present on the SmartInput
        assert textarea.provider == provider


def test_triggered_suggestion_provider_requires_trigger_and_provider():
    # Helper to satisfy Protocol types without functionality
    class DummyTrigger:
        def is_triggered(self, cursor_and_line):
            return False

    class DummyProvider:
        async def suggest(self, cursor_and_line):
            return SuggestionList([])

    trigger = DummyTrigger()
    provider = DummyProvider()

    # Valid construction
    autocomplete = TriggeredSuggestionProvider(trigger=trigger, provider=provider)
    assert autocomplete.trigger is trigger
    assert autocomplete.provider is provider

    # Invalid constructions
    with pytest.raises(ValueError, match="Trigger cannot be None"):
        TriggeredSuggestionProvider(
            trigger=cast(AutocompleteTrigger, None), provider=provider
        )

    with pytest.raises(ValueError, match="Provider cannot be None"):
        TriggeredSuggestionProvider(
            trigger=trigger, provider=cast(SuggestionProvider, None)
        )


@pytest.mark.asyncio
async def test_triggered_suggestion_provider_check_logic():
    class MockTrigger:
        def __init__(self, should_trigger):
            self.triggered = should_trigger

        def is_triggered(self, cursor_and_line):
            return self.triggered

    class MockProvider:
        async def suggest(self, cursor_and_line):
            return SuggestionList([SimpleSuggestion("s1")])

    cursor = CursorAndLine(Cursor(0, 0), "")

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
    names = [name for name, _ in suggestions]
    assert "/clear" in names
    assert "/model" in names


def test_get_autocomplete_suggestions_for_partial():
    registry = SlashCommandRegistry()

    suggestions = registry.get_matching_commands("/m")

    assert len(suggestions) == 1
    assert suggestions[0][0] == "/model"


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
    assert layout.offset.x == 7


def test_autocomplete_position_uses_above_when_no_room_below():
    screen_size = Size(80, 10)
    cursor_offset = Offset(10, 8)
    seed = CompletionSeed(cursor_offset, "ab")

    suggestions = SuggestionList([SimpleSuggestion("abc")])  # 1 item = height 1

    # Let's make it taller to force it above
    suggestions = SuggestionList(
        [SimpleSuggestion("abc") for _ in range(3)]
    )  # height 3

    layout = PopupLayout.calculate(suggestions, seed, screen_size)

    assert layout.offset.y == 5


def test_calculate_autocomplete_position_edge_cases():
    screen_size = Size(80, 24)

    # We need to simulate suggestions that result in specific size
    # height 5 -> 5 suggestions
    # width 20 -> max line length 18
    long_text = "a" * 18
    suggestions = SuggestionList([SimpleSuggestion(long_text) for _ in range(5)])

    cursor_offset = Offset(10, 5)
    seed = CompletionSeed(cursor_offset, "ab")  # width 2
    layout = PopupLayout.calculate(suggestions, seed, screen_size)

    assert layout.offset.y == 6
    assert layout.offset.x == 7

    # Test bottom edge
    cursor_offset = Offset(10, 20)
    seed = CompletionSeed(cursor_offset, "ab")
    layout = PopupLayout.calculate(suggestions, seed, screen_size)
    assert layout.offset.y == 15

    # Test right edge
    cursor_offset = Offset(75, 5)
    seed = CompletionSeed(
        cursor_offset, "ab"
    )  # start at 73. width 20. 73+20 = 93 > 80.
    layout = PopupLayout.calculate(suggestions, seed, screen_size)
    assert layout.offset.x == 60

    # Test left edge
    cursor_offset = Offset(1, 5)  # prefix 2 chars -> -1 -> 0
    seed = CompletionSeed(cursor_offset, "ab")
    layout = PopupLayout.calculate(suggestions, seed, screen_size)
    assert layout.offset.x == 0

    # Small screen
    small_screen = Size(80, 10)
    cursor_offset = Offset(10, 8)
    seed = CompletionSeed(cursor_offset, "ab")
    layout = PopupLayout.calculate(suggestions, seed, small_screen)
    assert layout.offset.y == 3


@pytest.mark.asyncio
async def test_submit_hides_autocomplete_popup(agent_task_manager):
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"), agent_task_manager)

    async with app.run_test() as pilot:
        # We need to find the input in the active workspace
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input

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
async def test_autocomplete_popup_keeps_initial_x_position(agent_task_manager):
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"), agent_task_manager)

    async with app.run_test() as pilot:
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input
        text_area.focus()

        # Type to show popup
        await pilot.press("/")
        await pilot.press("c")
        await pilot.pause()

        popup = app.query_one(AutocompletePopup)
        assert popup.display
        assert popup.offset is not None
        initial_x = popup.offset.x

        # Continue typing
        await pilot.press("l")
        await pilot.press("e")
        await pilot.pause()

        assert popup.offset is not None
        assert popup.offset.x == initial_x


@pytest.mark.asyncio
async def test_enter_key_selects_autocomplete_when_visible(agent_task_manager):
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"), agent_task_manager)

    async with app.run_test() as pilot:
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input
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
async def test_enter_key_submits_when_autocomplete_not_visible(agent_task_manager):
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"), agent_task_manager)

    async with app.run_test() as pilot:
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input
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
        strings = ["/short - desc", "/looooooong - description"]

        suggestions = [SimpleSuggestion(s) for s in strings]

        # Manually set state to simulate start() without async search
        # seed at 10,10, empty text (width 0) for simplicity
        seed = CompletionSeed(Offset(10, 10), "")

        popup.show(SuggestionList(suggestions), seed)

        await pilot.pause()

        assert popup.display is True
        assert popup.styles.width is not None
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
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input

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
async def test_submittable_text_area_file_search():
    from simple_agent.application.agent_task_manager import AgentTaskManager

    agent_task_manager = AgentTaskManager()
    # Mock searcher
    mock_searcher = AsyncMock()
    mock_searcher.search.return_value = ["my_file.py", "other_file.txt"]

    # Subclass TextualApp to inject dependencies
    class TestApp(TextualApp):
        def __init__(self, user_input, agent_id, agent_task_manager, **kwargs):
            super().__init__(user_input, agent_id, agent_task_manager, **kwargs)
            self.mock_searcher = AsyncMock()
            self.mock_searcher.search.return_value = ["my_file.py", "other_file.txt"]

        def compose(self):
            from textual.containers import Vertical

            from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

            with Vertical():
                provider = CompositeSuggestionProvider(
                    [
                        TriggeredSuggestionProvider(
                            trigger=AtSymbolTrigger(),
                            provider=FileSearchProvider(self.mock_searcher),
                        )
                    ]
                )
                yield AgentTabs(provider, self._root_agent_id, id="tabs")

    test_app = TestApp(StubUserInput(), AgentId("Agent"), agent_task_manager)

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
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input
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
        await pilot.press("backspace")  # delete /
        await pilot.press("/")
        await pilot.pause()
        await pilot.pause()  # Wait for async fetch

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
async def test_submittable_text_area_shift_enter(app: TextualApp):
    async with app.run_test() as pilot:
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input
        text_area.focus()
        text_area.text = "line1"
        text_area.move_cursor((0, 5))

        await pilot.press("shift+enter")
        await pilot.pause()

        assert text_area.text == "line1\n"
        # Ensure it didn't submit
        assert app.user_input is not None
        assert len(app.user_input.inputs) == 0


@pytest.mark.asyncio
async def test_submittable_text_area_ctrl_enter(app: TextualApp):
    async with app.run_test() as pilot:
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input
        text_area.focus()
        text_area.text = "line1"
        text_area.move_cursor((0, 5))

        await pilot.press("ctrl+enter")
        await pilot.pause()

        assert text_area.text == "line1\n"


@pytest.mark.asyncio
async def test_slash_command_argument_suggestions_appear():
    from simple_agent.application.slash_commands import SlashCommand as BaseSlashCommand

    class TestCommand(BaseSlashCommand):
        @property
        def name(self) -> str:
            return "/test"

        @property
        def description(self) -> str:
            return "Test command"

        async def accept(self, visitor) -> None:
            pass

    registry = SlashCommandRegistry()
    registry._commands["/test"] = TestCommand
    registry._arg_completers["/test"] = lambda: ["option1", "option2", "other"]
    provider = CompositeSuggestionProvider(
        [
            TriggeredSuggestionProvider(
                trigger=SlashCommandArgumentTrigger(),
                provider=SlashCommandArgumentProvider(registry),
            )
        ]
    )

    # Simulate input: "/test "
    line = "/test "
    cursor = Cursor(0, 6)  # At end of line
    cursor_and_line = CursorAndLine(cursor, line)

    # Check trigger manually
    trigger = SlashCommandArgumentTrigger()
    assert trigger.is_triggered(cursor_and_line) is True

    # Check suggestions
    suggestions = await provider.suggest(cursor_and_line)
    assert suggestions
    assert len(suggestions.suggestions) == 3
    assert suggestions.suggestions[0].display_text == "option1"


@pytest.mark.asyncio
async def test_slash_command_argument_filtering():
    from simple_agent.application.slash_commands import SlashCommand as BaseSlashCommand

    class TestCommand(BaseSlashCommand):
        @property
        def name(self) -> str:
            return "/test"

        @property
        def description(self) -> str:
            return "Test command"

        async def accept(self, visitor) -> None:
            pass

    registry = SlashCommandRegistry()
    registry._commands["/test"] = TestCommand
    registry._arg_completers["/test"] = lambda: ["option1", "option2", "other"]
    provider = CompositeSuggestionProvider(
        [
            TriggeredSuggestionProvider(
                trigger=SlashCommandArgumentTrigger(),
                provider=SlashCommandArgumentProvider(registry),
            )
        ]
    )

    # Simulate input: "/test op"
    line = "/test op"
    cursor = Cursor(0, 8)  # At end of line
    cursor_and_line = CursorAndLine(cursor, line)

    # Check suggestions
    suggestions = await provider.suggest(cursor_and_line)
    assert suggestions
    assert len(suggestions.suggestions) == 2
    assert suggestions.suggestions[0].display_text == "option1"
    assert suggestions.suggestions[1].display_text == "option2"


@pytest.mark.asyncio
async def test_slash_command_argument_no_trigger_if_no_space():
    # Simulate input: "/test" (no space yet)
    line = "/test"
    cursor = Cursor(0, 5)
    cursor_and_line = CursorAndLine(cursor, line)

    trigger = SlashCommandArgumentTrigger()
    assert trigger.is_triggered(cursor_and_line) is False


@pytest.mark.asyncio
async def test_model_command_integration():
    # Test with real registry and /model command
    registry = SlashCommandRegistry()  # Uses real ModelInfo
    provider = SlashCommandArgumentProvider(registry)
    trigger = SlashCommandArgumentTrigger()

    line = "/model "
    cursor = Cursor(0, 7)
    cursor_and_line = CursorAndLine(cursor, line)

    assert trigger.is_triggered(cursor_and_line) is True

    suggestions = await provider.suggest(cursor_and_line)
    assert suggestions
    # Verify at least one known model is present
    model_texts = [s.display_text for s in suggestions.suggestions]
    assert "gpt-5.1-codex" in model_texts


@pytest.mark.asyncio
async def test_popup_mounted_at_app_level(agent_task_manager):
    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"), agent_task_manager)

    async with app.run_test():
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input

        # Verify popup is mounted at screen level, not as child of SmartInput
        # (app.mount() actually mounts to the app's current screen)
        assert text_area.popup.parent == app.screen
        assert text_area.popup.parent != text_area

        # Verify popup can be queried from app
        popup_from_app = app.query_one(AutocompletePopup)
        assert popup_from_app == text_area.popup
