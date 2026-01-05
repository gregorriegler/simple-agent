import pytest
from textual.app import App, ComposeResult
from simple_agent.infrastructure.textual.smart_input import SmartInput
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    TriggeredSuggestionProvider, CompositeSuggestionProvider
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.slash_commands import (
    SlashCommandArgumentTrigger, SlashCommandArgumentProvider
)
from simple_agent.application.slash_command_registry import SlashCommandRegistry, SlashCommand

class MockApp(App):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def compose(self) -> ComposeResult:
        yield SmartInput(provider=self.provider)

@pytest.fixture
def registry():
    reg = SlashCommandRegistry()
    # Mocking arg_completer for a test command
    reg._commands["/test"] = SlashCommand(
        name="/test",
        description="Test command",
        arg_completer=lambda: ["option1", "option2", "other"]
    )
    return reg

@pytest.fixture
def provider(registry):
    return CompositeSuggestionProvider([
        TriggeredSuggestionProvider(
            trigger=SlashCommandArgumentTrigger(),
            provider=SlashCommandArgumentProvider(registry)
        )
    ])

@pytest.mark.asyncio
async def test_slash_command_argument_suggestions_appear(provider, registry):
    # Simulate input: "/test "
    from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import CursorAndLine, Cursor

    line = "/test "
    cursor = Cursor(0, 6) # At end of line
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
async def test_slash_command_argument_filtering(provider, registry):
    # Simulate input: "/test op"
    from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import CursorAndLine, Cursor

    line = "/test op"
    cursor = Cursor(0, 8) # At end of line
    cursor_and_line = CursorAndLine(cursor, line)

    # Check suggestions
    suggestions = await provider.suggest(cursor_and_line)
    assert suggestions
    assert len(suggestions.suggestions) == 2
    assert suggestions.suggestions[0].display_text == "option1"
    assert suggestions.suggestions[1].display_text == "option2"

@pytest.mark.asyncio
async def test_slash_command_argument_no_trigger_if_no_space(provider, registry):
    # Simulate input: "/test" (no space yet)
    from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import CursorAndLine, Cursor

    line = "/test"
    cursor = Cursor(0, 5)
    cursor_and_line = CursorAndLine(cursor, line)

    trigger = SlashCommandArgumentTrigger()
    assert trigger.is_triggered(cursor_and_line) is False

@pytest.mark.asyncio
async def test_model_command_integration():
    # Test with real registry and /model command
    registry = SlashCommandRegistry() # Uses real ModelInfo
    provider = SlashCommandArgumentProvider(registry)
    trigger = SlashCommandArgumentTrigger()

    from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import CursorAndLine, Cursor

    line = "/model "
    cursor = Cursor(0, 7)
    cursor_and_line = CursorAndLine(cursor, line)

    assert trigger.is_triggered(cursor_and_line) is True

    suggestions = await provider.suggest(cursor_and_line)
    assert suggestions
    # Verify at least one known model is present
    model_texts = [s.display_text for s in suggestions.suggestions]
    assert "gpt-5.1-codex" in model_texts
