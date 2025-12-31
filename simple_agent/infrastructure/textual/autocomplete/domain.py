from typing import Protocol, List, Optional
from dataclasses import dataclass, field

class FileReference:
    PREFIX = "[📦"
    SUFFIX = "]"

    @staticmethod
    def to_text(path: str) -> str:
        return f"{FileReference.PREFIX}{path}{FileReference.SUFFIX}"

    @staticmethod
    def is_present(text: str, path: str) -> bool:
         return FileReference.to_text(path) in text

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
        return {f for f in self.known_files if FileReference.is_present(self.text, f)}

@dataclass
class CompletionResult:
    text: str
    attachments: set[str] = field(default_factory=set)
    start_offset: Optional[int] = None

class Suggestion(Protocol):
    @property
    def display_text(self) -> str: ...

    def to_completion_result(self) -> CompletionResult: ...

@dataclass
class SuggestionList:
    suggestions: List[Suggestion]
    selected_index: int = 0

    def move_down(self) -> None:
        if not self.suggestions:
            return
        self.selected_index = (self.selected_index + 1) % len(self.suggestions)

    def move_up(self) -> None:
        if not self.suggestions:
            return
        self.selected_index = (self.selected_index - 1) % len(self.suggestions)

    def get_selection(self) -> Optional[CompletionResult]:
        if not self.suggestions:
            return None
        return self.suggestions[self.selected_index].to_completion_result()
