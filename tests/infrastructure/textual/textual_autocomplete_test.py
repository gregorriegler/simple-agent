import pytest
from textual.geometry import Offset, Size

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_app import (
    SubmittableTextArea,
    calculate_autocomplete_position,
)


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


class StubUserInput:
    def __init__(self) -> None:
        self.inputs = []

    def submit_input(self, content: str) -> None:
        self.inputs.append(content)


@pytest.mark.asyncio
async def test_submit_hides_autocomplete_popup():
    user_input = StubUserInput()
    app = TextualApp(user_input)

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
    app = TextualApp(user_input)

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
