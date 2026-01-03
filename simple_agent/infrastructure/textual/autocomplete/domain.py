from typing import Protocol, List, Optional, Set, Iterator, Tuple
from dataclasses import dataclass, field

@dataclass(frozen=True)
class FileReference:
    path: str

    PREFIX = "[📦"
    SUFFIX = "]"

    def to_text(self) -> str:
        return f"{self.PREFIX}{self.path}{self.SUFFIX}"

    def is_in(self, text: str) -> bool:
        return self.to_text() in text

@dataclass
class FileReferences:
    _references: set[FileReference] = field(default_factory=set)

    def add(self, paths: Set[str] | str) -> None:
        if isinstance(paths, str):
            self._references.add(FileReference(paths))
        else:
            self._references.update(FileReference(p) for p in paths)

    def clear(self) -> None:
        self._references.clear()

    def filter_active_in(self, text: str) -> "FileReferences":
        active_refs = {ref for ref in self._references if ref.is_in(text)}
        return FileReferences(active_refs)

    def __iter__(self) -> Iterator[FileReference]:
        return iter(self._references)

    def __len__(self) -> int:
        return len(self._references)

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

    @property
    def is_on_first_line(self) -> bool:
        return self.cursor.row == 0

class FileLoaderProtocol(Protocol):
    def read_file(self, file_path_str: str) -> Optional[str]: ...

class FileContextFormatterProtocol(Protocol):
    def format(self, loaded_files: List[Tuple[str, str]]) -> str: ...

@dataclass
class CompletionResult:
    text: str
    files: FileReferences

    @property
    def active_files(self) -> "FileReferences":
        return self.files.filter_active_in(self.text)

    def expand(self, file_loader: FileLoaderProtocol, formatter: FileContextFormatterProtocol) -> str:
        content = self.text.strip()
        active_references = self.active_files

        if active_references:
            loaded_files = []
            for file_ref in active_references:
                file_path_str = file_ref.path
                file_text = file_loader.read_file(file_path_str)
                if file_text is not None:
                    loaded_files.append((file_path_str, file_text))

            file_contents = formatter.format(loaded_files)

            if file_contents:
                content += "\n" + file_contents

        return content

class Suggestion(Protocol):
    @property
    def display_text(self) -> str: ...

    def to_completion_result(self) -> CompletionResult: ...

@dataclass
class SuggestionList:
    suggestions: List[Suggestion]
    selected_index: int = 0

    def __bool__(self) -> bool:
        return bool(self.suggestions)

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
