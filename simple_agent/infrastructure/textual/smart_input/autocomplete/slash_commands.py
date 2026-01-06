from typing import Any

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.smart_input.autocomplete import (
    AutocompleteTrigger,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    CompletionResult,
    CursorAndLine,
    SuggestionList,
)


class SlashCommandSuggestion:
    def __init__(self, command: Any):
        self.command = command

    @property
    def display_text(self) -> str:
        return f"{self.command.name} - {self.command.description}"

    def to_completion_result(self) -> CompletionResult:
        return CompletionResult(text=self.command.name + " ")


class SlashAtStartOfLineTrigger(AutocompleteTrigger):
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


class SlashCommandArgSuggestion:
    def __init__(self, argument: str):
        self.argument = argument

    @property
    def display_text(self) -> str:
        return self.argument

    def to_completion_result(self) -> CompletionResult:
        return CompletionResult(text=self.argument)


class SlashCommandArgumentTrigger(AutocompleteTrigger):
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        # Must be on first line for slash commands
        if not cursor_and_line.is_on_first_line:
            return False

        line = cursor_and_line.line
        # Must start with a slash
        if not line.startswith("/"):
            return False

        parts = line.split(" ", 1)
        # Must have a command part and a space
        if len(parts) < 2:
            # Check if we have a trailing space if parts didn't split (e.g. "/model ")
            # " ".split(" ", 1) -> ['', '']
            # "/model ".split(" ", 1) -> ['/model', '']
            # "/model".split(" ", 1) -> ['/model']
            if line.endswith(" "):
                return True
            return False

        # If we have parts[1], we are in the argument section.
        # But wait, CursorAndLine.word logic separates by space.
        # If I type "/model ", word is "" (empty string after space).
        # If I type "/model gpt", word is "gpt".

        # We need to make sure the cursor is NOT in the first word (the command itself).
        first_space_index = line.find(" ")
        if first_space_index == -1:
            return False

        if cursor_and_line.cursor.col > first_space_index:
            return True

        return False


class SlashCommandArgumentProvider:
    def __init__(self, registry: SlashCommandRegistry):
        self.registry = registry

    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        line = cursor_and_line.line
        parts = line.split(" ", 1)
        command_name = parts[0]

        command = self.registry.get_command(command_name)
        if not command or not command.arg_completer:
            return SuggestionList([])

        candidates = command.arg_completer()
        query = cursor_and_line.word

        filtered = [
            SlashCommandArgSuggestion(cand)
            for cand in candidates
            if cand.startswith(query)
        ]

        return SuggestionList(filtered)
