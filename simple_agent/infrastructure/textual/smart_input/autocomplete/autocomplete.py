from dataclasses import dataclass, field
import re
from typing import Protocol, List, Optional, Set, Iterator


class FileLoader(Protocol):
    def read_file(self, file_path_str: str) -> Optional[str]: ...

@dataclass(frozen=True)
class FileReference:
    path: str

    PREFIX = "[📦"
    SUFFIX = "]"

    def to_text(self) -> str:
        return f"{self.PREFIX}{self.path}{self.SUFFIX}"

    def is_in(self, text: str) -> bool:
        return self.to_text() in text

    def load_content(self, loader: FileLoader) -> Optional[str]:
        return loader.read_file(self.path)

@dataclass
class FileReferences:
    _references: set[FileReference] = field(default_factory=set)

    @classmethod
    def from_text(cls, text: str) -> "FileReferences":
        pattern = re.escape(FileReference.PREFIX) + r"(.*?)" + re.escape(FileReference.SUFFIX)
        matches = re.findall(pattern, text)
        refs = cls()
        refs.add(set(matches))
        return refs

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

    def load_all(self, loader: FileLoader) -> List[str]:
        loaded = []
        for ref in self._references:
            content = ref.load_content(loader)
            if content is not None:
                loaded.append(content)
        return loaded

@dataclass(frozen=True)
class Cursor:
    row: int
    col: int

@dataclass
class CursorAndLine:
    cursor: Cursor
    line: str

    @property
    def word(self) -> str:
        text_before = self.line[:self.cursor.col]
        last_space_index = text_before.rfind(" ")
        start_index = last_space_index + 1
        return text_before[start_index:]

    @property
    def word_start_index(self) -> int:
        text_before = self.line[:self.cursor.col]
        last_space_index = text_before.rfind(" ")
        return last_space_index + 1

    @property
    def is_on_first_line(self) -> bool:
        return self.cursor.row == 0

@dataclass
class CompletionResult:
    text: str
    files: FileReferences

    @property
    def active_files(self) -> FileReferences:
        return self.files.filter_active_in(self.text)

    def expand(self, file_loader: FileLoader) -> str:
        content = self.text.strip()
        loaded_files = self.active_files.load_all(file_loader)
        file_contents = "\n".join(loaded_files)

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


class AutocompleteTrigger(Protocol):
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        ...

class SuggestionProvider(Protocol):
    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        ...

@dataclass
class TriggeredSuggestionProvider(SuggestionProvider):
    trigger: AutocompleteTrigger
    provider: SuggestionProvider

    def __post_init__(self):
        if self.trigger is None:
            raise ValueError("Trigger cannot be None")
        if self.provider is None:
            raise ValueError("Provider cannot be None")

    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        if self.trigger.is_triggered(cursor_and_line):
            return await self.provider.suggest(cursor_and_line)
        return SuggestionList([])

class CompositeSuggestionProvider(SuggestionProvider):
    def __init__(self, providers: List[SuggestionProvider] = None):
        self._providers = providers or []

    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        for provider in self._providers:
            suggestion_list = await provider.suggest(cursor_and_line)
            if suggestion_list:
                return suggestion_list
        return SuggestionList([])

    def __iter__(self) -> Iterator[SuggestionProvider]:
        return iter(self._providers)