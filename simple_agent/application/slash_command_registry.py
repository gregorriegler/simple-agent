from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class SlashCommand:
    name: str
    description: str
    handler: Callable[[str, Any], Awaitable[Any] | Any]
    arg_completer: Callable[[], list[str]] | None = None


class SlashCommandRegistry:
    def __init__(self):
        self._commands: dict[str, SlashCommand] = {}

    def register(self, command: SlashCommand):
        self._commands[command.name] = command

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
