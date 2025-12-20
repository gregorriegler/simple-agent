from dataclasses import dataclass
from typing import Callable


@dataclass
class SlashCommand:
    name: str
    description: str
    arg_completer: Callable[[], list[str]] | None = None


class SlashCommandRegistry:
    def __init__(self):
        self._commands = {
            "/clear": SlashCommand(
                name="/clear",
                description="Clear conversation history"
            ),
            "/model": SlashCommand(
                name="/model",
                description="Change model"
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