from typing import Protocol, List, Any, Optional
from dataclasses import dataclass, field
import logging

from textual.geometry import Offset, Size

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.file_search import FileSearcher

logger = logging.getLogger(__name__)

@dataclass
class PopupAnchor:
    """Encapsulates the visual state needed to position the popup."""
    cursor_offset: Offset
    screen_size: Size

    def get_placement(self, popup_size: Size) -> Offset:
        """
        Calculate the best position for the popup given its size.
        """
        popup_height = popup_size.height
        popup_width = popup_size.width

        if popup_height < 1:
            popup_height = 1
        if popup_width < 1:
            popup_width = 1

        below_y = self.cursor_offset.y + 1
        above_y = self.cursor_offset.y - popup_height

        # Default to below if it fits, otherwise try above, else clamp
        if below_y + popup_height <= self.screen_size.height:
            y = below_y
        elif above_y >= 0:
            y = above_y
        else:
            y = max(0, min(below_y, self.screen_size.height - popup_height))

        # Horizontal positioning
        anchor_x = self.cursor_offset.x - 2
        max_x = max(0, self.screen_size.width - popup_width)
        x = min(max(anchor_x, 0), max_x)

        return Offset(x, y)

    @property
    def max_width(self) -> int:
        return self.screen_size.width

@dataclass
class WordAtCursor:
    word: str
    start_index: int

    @staticmethod
    def from_cursor(line: str, col: int) -> "WordAtCursor":
        text_before = line[:col]
        last_space_index = text_before.rfind(" ")
        start_index = last_space_index + 1
        word = text_before[start_index:]
        return WordAtCursor(word, start_index)

@dataclass
class CursorAndLine:
    row: int
    col: int
    line: str

    @property
    def current_word(self) -> WordAtCursor:
        return WordAtCursor.from_cursor(self.line, self.col)

@dataclass
class MessageDraft:
    text: str
    known_files: set[str] = field(default_factory=set)

    @property
    def active_files(self) -> set[str]:
        return {f for f in self.known_files if f"[📦{f}]" in self.text}

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

    def is_triggered(self) -> bool:
        """
        Returns True if this search was actively triggered by the input context.
        """
        ...

class Autocompleter(Protocol):
    def check(self, cursor_and_line: CursorAndLine) -> CompletionSearch:
        """
        Check if autocomplete should be triggered.
        Returns a CompletionSearch object (which may be a NoOpSearch).
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

class NoOpSearch:
    async def get_suggestions(self) -> List[Suggestion]:
        return []

    def is_triggered(self) -> bool:
        return False

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

class FileSearchAutocompleter:
    def __init__(self, searcher: FileSearcher):
        self.searcher = searcher

    def check(self, cursor_and_line: CursorAndLine) -> CompletionSearch:
        word = cursor_and_line.current_word
        if word.word.startswith("@"):
             return FileSearch(query=word.word[1:], start_index=word.start_index, searcher=self.searcher)
        return NoOpSearch()

class CompositeAutocompleter:
    def __init__(self, autocompleters: List[Autocompleter]):
        self.autocompleters = autocompleters

    def check(self, cursor_and_line: CursorAndLine) -> CompletionSearch:
        for autocompleter in self.autocompleters:
            search = autocompleter.check(cursor_and_line)
            if search.is_triggered():
                return search
        return NoOpSearch()
