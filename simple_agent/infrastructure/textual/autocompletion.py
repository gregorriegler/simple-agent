from typing import Protocol, List, Any, Optional
from dataclasses import dataclass, field
import logging

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.file_search import FileSearcher

logger = logging.getLogger(__name__)

@dataclass
class AutocompleteRequest:
    query: str
    start_index: int
    trigger_char: str

@dataclass
class CompletionResult:
    text: str
    attachments: set[str] = field(default_factory=set)
    start_offset: Optional[int] = None

class Suggestion(Protocol):
    @property
    def display_text(self) -> str: ...

    def to_completion_result(self) -> CompletionResult: ...

class Autocompleter(Protocol):
    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteRequest]:
        """
        Check if autocomplete should be triggered.
        Returns request if triggered, None otherwise.
        """
        ...

    async def get_suggestions(self, request: AutocompleteRequest) -> List[Suggestion]:
        """
        Get list of suggestions based on request.
        """
        ...

@dataclass
class SlashCommandSuggestion:
    command: Any # SlashCommand

    @property
    def display_text(self) -> str:
        return f"{self.command.name} - {self.command.description}"

    def to_completion_result(self) -> CompletionResult:
        return CompletionResult(text=self.command.name + " ")

@dataclass
class FileSuggestion:
    file_path: str

    @property
    def display_text(self) -> str:
        return self.file_path

    def to_completion_result(self) -> CompletionResult:
         display_marker = f"[📦{self.file_path}] "
         return CompletionResult(text=display_marker, attachments={self.file_path})


class SlashCommandAutocompleter:
    def __init__(self, registry: SlashCommandRegistry):
        self.registry = registry

    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteRequest]:
        if row == 0 and col > 0 and line.startswith("/") and " " not in line[:col]:
            return AutocompleteRequest(query=line[:col], start_index=0, trigger_char="/")
        return None

    async def get_suggestions(self, request: AutocompleteRequest) -> List[Suggestion]:
        commands = self.registry.get_matching_commands(request.query)
        return [SlashCommandSuggestion(cmd) for cmd in commands]


class FileSearchAutocompleter:
    def __init__(self, searcher: FileSearcher):
        self.searcher = searcher

    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteRequest]:
        # Check for file search (@)
        text_before_cursor = line[:col]

        # Find the start of the word before cursor
        last_space_index = text_before_cursor.rfind(" ")
        word_start_index = last_space_index + 1
        current_word = text_before_cursor[word_start_index:]

        if current_word.startswith("@"):
             return AutocompleteRequest(query=current_word[1:], start_index=word_start_index, trigger_char="@")
        return None

    async def get_suggestions(self, request: AutocompleteRequest) -> List[Suggestion]:
        try:
            results = await self.searcher.search(request.query)
            return [FileSuggestion(str(res)) for res in results]
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return []
