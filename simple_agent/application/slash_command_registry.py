from collections.abc import Callable

from simple_agent.application.model_info import ModelInfo
from simple_agent.application.slash_commands import (
    ClearCommand,
    ModelCommand,
    SlashCommand,
)


class CommandParseError(Exception):
    pass


class SlashCommandRegistry:
    def __init__(self, available_models: list[str] | None = None):
        if available_models is None:
            available_models = list(ModelInfo.KNOWN_MODELS.keys())

        self._available_models = available_models
        self._commands: dict[str, type[SlashCommand]] = {
            "/clear": ClearCommand,
            "/model": ModelCommand,
        }
        self._arg_completers: dict[str, Callable[[], list[str]]] = {
            "/model": lambda: available_models,
        }

    def get_all_commands(self) -> list[str]:
        return list(self._commands.keys())

    def get_matching_commands(self, prefix: str) -> list[tuple[str, str]]:
        if prefix == "/":
            return [
                (name, self._get_command_instance(cmd_class).description)
                for name, cmd_class in self._commands.items()
            ]

        matching = []
        for name, cmd_class in self._commands.items():
            if name.startswith(prefix):
                matching.append(
                    (name, self._get_command_instance(cmd_class).description)
                )

        return matching

    def get_command(self, name: str) -> tuple[str, str] | None:
        cmd_class = self._commands.get(name)
        if cmd_class:
            instance = self._get_command_instance(cmd_class)
            return (instance.name, instance.description)
        return None

    def get_arg_completer(self, command_name: str) -> Callable[[], list[str]] | None:
        return self._arg_completers.get(command_name)

    def parse(self, command_line: str) -> SlashCommand:
        parts = command_line.split()
        if not parts:
            raise CommandParseError("Empty command")

        command_name = parts[0]
        args = parts[1:]

        if command_name == "/clear":
            if args:
                raise CommandParseError("/clear does not take arguments")
            return ClearCommand()
        elif command_name == "/model":
            if len(args) != 1:
                raise CommandParseError("Usage: /model <model-name>")
            return ModelCommand(args[0])
        else:
            raise CommandParseError(f"Unknown command: {command_name}")

    def _get_command_instance(self, cmd_class: type[SlashCommand]) -> SlashCommand:
        if cmd_class == ModelCommand:
            return ModelCommand("dummy")
        return cmd_class()
