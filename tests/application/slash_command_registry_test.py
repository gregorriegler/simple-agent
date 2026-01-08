import pytest

from simple_agent.application.slash_command_registry import (
    CommandParseError,
    SlashCommandRegistry,
)
from simple_agent.application.slash_commands import ClearCommand, ModelCommand


def test_registry_returns_all_commands():
    registry = SlashCommandRegistry()
    commands = registry.get_all_commands()

    assert "/clear" in commands
    assert "/model" in commands


def test_registry_filters_commands_by_prefix():
    registry = SlashCommandRegistry()

    # Test filtering with "/m"
    matches = registry.get_matching_commands("/m")
    assert len(matches) == 1
    assert matches[0][0] == "/model"
    assert matches[0][1] == "Change model"


def test_registry_returns_all_on_slash_only():
    registry = SlashCommandRegistry()
    matches = registry.get_matching_commands("/")

    assert len(matches) == 2
    names = [name for name, _ in matches]
    assert "/clear" in names
    assert "/model" in names


def test_registry_returns_empty_for_no_matches():
    registry = SlashCommandRegistry()
    matches = registry.get_matching_commands("/xyz")

    assert len(matches) == 0


def test_slash_command_has_description():
    registry = SlashCommandRegistry()
    matches = registry.get_matching_commands("/clear")

    assert len(matches) == 1
    assert matches[0][1] == "Clear conversation history"


def test_model_command_has_description():
    registry = SlashCommandRegistry()
    matches = registry.get_matching_commands("/model")

    assert len(matches) == 1
    assert matches[0][1] == "Change model"


def test_registry_get_command_returns_metadata():
    registry = SlashCommandRegistry()
    result = registry.get_command("/clear")

    assert result is not None
    assert result[0] == "/clear"
    assert result[1] == "Clear conversation history"


def test_registry_get_arg_completer():
    registry = SlashCommandRegistry(available_models=["model1", "model2"])
    completer = registry.get_arg_completer("/model")

    assert completer is not None
    assert completer() == ["model1", "model2"]


def test_parse_clear_command():
    registry = SlashCommandRegistry()
    command = registry.parse("/clear")

    assert isinstance(command, ClearCommand)


def test_parse_clear_command_with_args_raises_error():
    registry = SlashCommandRegistry()

    with pytest.raises(CommandParseError, match="does not take arguments"):
        registry.parse("/clear foo")


def test_parse_model_command():
    registry = SlashCommandRegistry()
    command = registry.parse("/model gpt-4")

    assert isinstance(command, ModelCommand)
    assert command.model_name == "gpt-4"


def test_parse_model_command_without_args_raises_error():
    registry = SlashCommandRegistry()

    with pytest.raises(CommandParseError, match="Usage: /model"):
        registry.parse("/model")


def test_parse_unknown_command_raises_error():
    registry = SlashCommandRegistry()

    with pytest.raises(CommandParseError, match="Unknown command"):
        registry.parse("/unknown")


def test_parse_empty_command_raises_error():
    registry = SlashCommandRegistry()

    with pytest.raises(CommandParseError, match="Empty command"):
        registry.parse("")
