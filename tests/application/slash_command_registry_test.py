from simple_agent.application.slash_command_registry import (
    SlashCommand,
    SlashCommandRegistry,
)


async def dummy_handler(args, agent):
    pass


def test_registry_returns_all_commands():
    registry = SlashCommandRegistry()
    registry.register(
        SlashCommand("/clear", "Clear conversation history", dummy_handler)
    )
    registry.register(SlashCommand("/model", "Change model", dummy_handler))

    commands = registry.get_all_commands()

    assert "/clear" in commands
    assert "/model" in commands


def test_registry_filters_commands_by_prefix():
    registry = SlashCommandRegistry()
    registry.register(SlashCommand("/model", "Change model", dummy_handler))

    # Test filtering with "/m"
    matches = registry.get_matching_commands("/m")
    assert len(matches) == 1
    assert matches[0].name == "/model"


def test_registry_returns_all_on_slash_only():
    registry = SlashCommandRegistry()
    registry.register(
        SlashCommand("/clear", "Clear conversation history", dummy_handler)
    )
    registry.register(SlashCommand("/model", "Change model", dummy_handler))

    matches = registry.get_matching_commands("/")

    assert len(matches) == 2
    assert any(cmd.name == "/clear" for cmd in matches)
    assert any(cmd.name == "/model" for cmd in matches)


def test_registry_returns_empty_for_no_matches():
    registry = SlashCommandRegistry()
    matches = registry.get_matching_commands("/xyz")

    assert len(matches) == 0


def test_slash_command_has_description():
    registry = SlashCommandRegistry()
    registry.register(
        SlashCommand("/clear", "Clear conversation history", dummy_handler)
    )
    matches = registry.get_matching_commands("/clear")

    assert len(matches) == 1
    assert matches[0].description == "Clear conversation history"


def test_slash_command_dataclass_has_name_and_description():
    cmd = SlashCommand(name="/test", description="Test command", handler=dummy_handler)

    assert cmd.name == "/test"
    assert cmd.description == "Test command"
    assert cmd.arg_completer is None


def test_slash_command_with_arg_completer():
    def dummy_completer():
        return ["arg1", "arg2"]

    cmd = SlashCommand(
        name="/test",
        description="Test command",
        handler=dummy_handler,
        arg_completer=dummy_completer,
    )

    assert cmd.arg_completer is not None
    assert cmd.arg_completer() == ["arg1", "arg2"]
