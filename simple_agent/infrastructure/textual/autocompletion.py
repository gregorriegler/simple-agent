from typing import Protocol, List, Any, Optional
from dataclasses import dataclass, field
import logging

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.file_search import FileSearcher

logger = logging.getLogger(__name__)

@dataclass
class CursorAndLine:
    row: int
    col: int
    line: str

    @property
    def text_before_cursor(self) -> str:
        return self.line[:self.col]

    @property
    def word_before_cursor(self) -> str:
        text = self.text_before_cursor
        last_space_index = text.rfind(" ")
        return text[last_space_index + 1:]

    @property
    def word_start_index(self) -> int:
        text = self.text_before_cursor
        last_space_index = text.rfind(" ")
        return last_space_index + 1

@dataclass
class CompletionResult:
    text: str
    attachments: set[str] = field(default_factory=set)
    start_offset: Optional[int] = None

class Suggestion(Protocol):
    @property
    def display_text(self) -> str: ...

    def to_completion_result(self) -> CompletionResult: ...

class CompletionSearch(Protocol):
    async def get_suggestions(self) -> List[Suggestion]:
        """
        Get list of suggestions for this search.
        """
        ...

class Autocompleter(Protocol):
    def check(self, cursor_and_line: CursorAndLine) -> Optional[CompletionSearch]:
        """
        Check if autocomplete should be triggered.
        Returns a search object if triggered, None otherwise.
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

class SlashCommandSearch:
    def __init__(self, query: str, start_index: int, registry: SlashCommandRegistry):
        self.query = query
        self.start_index = start_index
        self.registry = registry

    async def get_suggestions(self) -> List[Suggestion]:
        commands = self.registry.get_matching_commands(self.query)
        return [SlashCommandSuggestion(cmd, self.start_index) for cmd in commands]

class FileSearch:
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

    def check(self, cursor_and_line: CursorAndLine) -> Optional[CompletionSearch]:
        if cursor_and_line.row == 0 and cursor_and_line.col > 0 and cursor_and_line.line.startswith("/") and " " not in cursor_and_line.text_before_cursor:
            return SlashCommandSearch(query=cursor_and_line.text_before_cursor, start_index=0, registry=self.registry)
        return None

class FileSearchAutocompleter:
    def __init__(self, searcher: FileSearcher):
        self.searcher = searcher

    def check(self, cursor_and_line: CursorAndLine) -> Optional[CompletionSearch]:
        # Check for file search (@)
        current_word = cursor_and_line.word_before_cursor

        if current_word.startswith("@"):
             return FileSearch(query=current_word[1:], start_index=cursor_and_line.word_start_index, searcher=self.searcher)
        return None
