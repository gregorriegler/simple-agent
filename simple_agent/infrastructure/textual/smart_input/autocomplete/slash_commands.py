from typing import List, Any

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.smart_input.autocomplete.domain import (
    Suggestion, CompletionResult, CursorAndLine, FileReferences, SuggestionList
)


class SlashCommandSuggestion:
    def __init__(self, command: Any):
        self.command = command

    @property
    def display_text(self) -> str:
        return f"{self.command.name} - {self.command.description}"

    def to_completion_result(self) -> CompletionResult:
        return CompletionResult(
            text=self.command.name + " ",
            files=FileReferences(),
        )

class SlashAtStartOfLineTrigger:
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        return (
            cursor_and_line.is_on_first_line
            and cursor_and_line.word_start_index == 0
            and cursor_and_line.word.startswith("/")
        )

class SlashCommandProvider:
    def __init__(self, registry: SlashCommandRegistry):
        self.registry = registry

    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        query = cursor_and_line.word
        commands = self.registry.get_matching_commands(query)
        return SuggestionList([SlashCommandSuggestion(cmd) for cmd in commands])
