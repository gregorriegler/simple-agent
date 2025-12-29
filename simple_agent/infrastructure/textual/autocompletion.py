from typing import Protocol, List, Any, Optional
from dataclasses import dataclass, field
import logging

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.file_search import FileSearcher

logger = logging.getLogger(__name__)

@dataclass
class CompletionResult:
    text: str
    attachments: set[str] = field(default_factory=set)
    start_offset: Optional[int] = None

class Suggestion(Protocol):
    @property
    def display_text(self) -> str: ...

    def to_completion_result(self) -> CompletionResult: ...

class AutocompleteContext(Protocol):
    async def get_suggestions(self) -> List[Suggestion]:
        """
        Get list of suggestions for this context.
        """
        ...

class Autocompleter(Protocol):
    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteContext]:
        """
        Check if autocomplete should be triggered.
        Returns a context if triggered, None otherwise.
        """
        ...

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

@dataclass
class FileSuggestion:
    file_path: str
    start_index: int

    @property
    def display_text(self) -> str:
        return self.file_path

    def to_completion_result(self) -> CompletionResult:
         display_marker = f"[📦{self.file_path}] "
         return CompletionResult(
             text=display_marker,
             attachments={self.file_path},
             start_offset=self.start_index
         )

class SlashCommandContext:
    def __init__(self, query: str, start_index: int, registry: SlashCommandRegistry):
        self.query = query
        self.start_index = start_index
        self.registry = registry

    async def get_suggestions(self) -> List[Suggestion]:
        commands = self.registry.get_matching_commands(self.query)
        return [SlashCommandSuggestion(cmd, self.start_index) for cmd in commands]

class FileSearchContext:
    def __init__(self, query: str, start_index: int, searcher: FileSearcher):
        self.query = query
        self.start_index = start_index
        self.searcher = searcher

    async def get_suggestions(self) -> List[Suggestion]:
        try:
            results = await self.searcher.search(self.query)
            return [FileSuggestion(str(res), self.start_index) for res in results]
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return []

class SlashCommandAutocompleter:
    def __init__(self, registry: SlashCommandRegistry):
        self.registry = registry

    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteContext]:
        if row == 0 and col > 0 and line.startswith("/") and " " not in line[:col]:
            return SlashCommandContext(query=line[:col], start_index=0, registry=self.registry)
        return None

class FileSearchAutocompleter:
    def __init__(self, searcher: FileSearcher):
        self.searcher = searcher

    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteContext]:
        # Check for file search (@)
        text_before_cursor = line[:col]

        # Find the start of the word before cursor
        last_space_index = text_before_cursor.rfind(" ")
        word_start_index = last_space_index + 1
        current_word = text_before_cursor[word_start_index:]

        if current_word.startswith("@"):
             return FileSearchContext(query=current_word[1:], start_index=word_start_index, searcher=self.searcher)
        return None
