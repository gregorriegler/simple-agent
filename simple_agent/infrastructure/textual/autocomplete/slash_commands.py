from typing import List, Any
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.autocomplete.domain import (
    Suggestion, CompletionResult, CursorAndLine
)
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteTrigger, SuggestionProvider
)

class SlashCommandSuggestion:
    def __init__(self, command: Any, start_index: int):
        self.command = command
        self.start_index = start_index

    @property
    def display_text(self) -> str:
        return f"{self.command.name} - {self.command.description}"

    def to_completion_result(self) -> CompletionResult:
        return CompletionResult(
            text=self.command.name + " ",
            start_offset=self.start_index
        )

class SlashAtStartOfLineTrigger:
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        if cursor_and_line.cursor.row == 0 and cursor_and_line.cursor.col > 0:
            word = cursor_and_line.current_word
            return word.start_index == 0 and word.word.startswith("/")
        return False

class SlashCommandProvider:
    def __init__(self, registry: SlashCommandRegistry):
        self.registry = registry

    async def fetch(self, cursor_and_line: CursorAndLine) -> List[Suggestion]:
        word = cursor_and_line.current_word
        query = word.word
        # start_index is implicit from the word logic, but we pass it to suggestion
        commands = self.registry.get_matching_commands(query)
        return [SlashCommandSuggestion(cmd, word.start_index) for cmd in commands]
