from collections.abc import Callable
from dataclasses import dataclass

from simple_agent.application.model_info import ModelInfo


@dataclass
class SlashCommand:
    name: str
    description: str
    arg_completer: Callable[[], list[str]] | None = None


class SlashCommandRegistry:
    def __init__(
        self,
        available_models: list[str] | None = None,
        available_agents: list[str] | None = None,
    ):
        if available_models is None:
            available_models = list(ModelInfo.KNOWN_MODELS.keys())
        if available_agents is None:
            available_agents = []

        self._commands = {
            "/clear": SlashCommand(
                name="/clear", description="Clear conversation history"
            ),
            "/model": SlashCommand(
                name="/model",
                description="Change model",
                arg_completer=lambda: available_models,
            ),
            "/agent": SlashCommand(
                name="/agent",
                description="Change agent",
                arg_completer=lambda: available_agents,
            ),
        }

    def get_all_commands(self) -> list[str]:
        """Returns a list of all command names."""
        return list(self._commands.keys())

    def get_matching_commands(self, prefix: str) -> list[SlashCommand]:
        """Returns commands that match the given prefix."""
        if prefix == "/":
            # Return all commands when only "/" is typed
            return list(self._commands.values())

        matching = []
        for name, cmd in self._commands.items():
            if name.startswith(prefix):
                matching.append(cmd)

        return matching

    def get_command(self, name: str) -> SlashCommand | None:
        """Returns a command by name, or None if not found."""
        return self._commands.get(name)
