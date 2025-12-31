from dataclasses import dataclass
from typing import List, Any
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.autocomplete.domain import (
    Suggestion, CompletionResult, CursorAndLine
)
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    Autocompleter, CompletionSearch, NoOpSearch
)

@dataclass
class SlashCommandSuggestion:
    command: Any # SlashCommand
    start_index: int

    @property
    def display_text(self) -> str:
        return f"{self.command.name} - {self.command.description}"

    def to_completion_result(self) -> CompletionResult:
        return CompletionResult(
            text=self.command.name + " ",
            start_offset=self.start_index
        )

class SlashCommandSearch:
    def __init__(self, query: str, start_index: int, registry: SlashCommandRegistry):
        self.query = query
        self.start_index = start_index
        self.registry = registry

    async def get_suggestions(self) -> List[Suggestion]:
        commands = self.registry.get_matching_commands(self.query)
        return [SlashCommandSuggestion(cmd, self.start_index) for cmd in commands]

    def is_triggered(self) -> bool:
        return True

class SlashCommandAutocompleter:
    def __init__(self, registry: SlashCommandRegistry):
        self.registry = registry

    def check(self, cursor_and_line: CursorAndLine) -> CompletionSearch:
        if cursor_and_line.row == 0 and cursor_and_line.col > 0:
            word = cursor_and_line.current_word
            if word.start_index == 0 and word.word.startswith("/"):
                return SlashCommandSearch(query=word.word, start_index=0, registry=self.registry)
        return NoOpSearch()
