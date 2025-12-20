import pytest
from textual.widgets import TextArea

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.textual_app import SubmittableTextArea


pytestmark = pytest.mark.asyncio


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