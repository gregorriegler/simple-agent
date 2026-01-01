from typing import Protocol, List, Optional, Set
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
class FileReferences:
    _paths: set[str] = field(default_factory=set)

    def add(self, paths: Set[str] | str) -> None:
        if isinstance(paths, str):
            self._paths.add(paths)
        else:
            self._paths.update(paths)

    def clear(self) -> None:
        self._paths.clear()

    def filter_active_in(self, text: str) -> set[str]:
         return {f for f in self._paths if FileReference.is_present(text, f)}

    def __iter__(self):
        return iter(self._paths)

    def __len__(self):
        return len(self._paths)

@dataclass(frozen=True)
class Cursor:
    row: int
    col: int

@dataclass
class CursorAndLine:
    cursor: Cursor
    line: str

    @property
    def _word_context(self) -> tuple[str, int]:
        text_before = self.line[:self.cursor.col]
        last_space_index = text_before.rfind(" ")
        start_index = last_space_index + 1
        word = text_before[start_index:]
        return word, start_index

    @property
    def word(self) -> str:
        return self._word_context[0]

    @property
    def word_start_index(self) -> int:
        return self._word_context[1]

@dataclass
class MessageDraft:
    text: str
    files: FileReferences

    @property
    def active_files(self) -> set[str]:
        return self.files.filter_active_in(self.text)

@dataclass
class CompletionResult:
    text: str
    attachments: set[str] = field(default_factory=set)
    start_offset: int = 0

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

    @property
    def max_content_width(self) -> int:
        if not self.suggestions:
            return 0
        return max(len(s.display_text) for s in self.suggestions)

    def get_display_lines(self, width: int) -> List[str]:
        return [s.display_text[:width] for s in self.suggestions]
