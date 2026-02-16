from collections.abc import Callable

from simple_agent.application.model_info import ModelInfo
from simple_agent.application.slash_commands import (
    AgentCommand,
    ClearCommand,
    ModelCommand,
    SlashCommand,
)


class CommandParseError(Exception):
    pass


class SlashCommandRegistry:
    def __init__(
        self,
        available_models: list[str] | None = None,
        available_agents: list[str] | None = None,
    ):
        if available_models is None:
            available_models = list(ModelInfo.KNOWN_MODELS.keys())

        self._available_models = available_models
        self._available_agents = available_agents
        self._commands: dict[str, type[SlashCommand]] = {
            "/clear": ClearCommand,
            "/model": ModelCommand,
        }
        self._arg_completers: dict[str, Callable[[], list[str]]] = {
            "/model": lambda: available_models,
        }
        if available_agents is not None:
            self._commands["/agent"] = AgentCommand
            self._arg_completers["/agent"] = lambda: available_agents

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
        elif command_name == "/agent":
            if len(args) != 1:
                raise CommandParseError("Usage: /agent <agent-name>")
            if self._available_agents is None or args[0] not in self._available_agents:
                raise CommandParseError(f"Unknown agent: {args[0]}")
            return AgentCommand(args[0])
        else:
            raise CommandParseError(f"Unknown command: {command_name}")

    def _get_command_instance(self, cmd_class: type[SlashCommand]) -> SlashCommand:
        if cmd_class == ModelCommand:
            return ModelCommand("dummy")
        if cmd_class == AgentCommand:
            return AgentCommand("dummy")
        return cmd_class()
