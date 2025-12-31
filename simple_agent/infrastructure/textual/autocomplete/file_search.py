from dataclasses import dataclass
from typing import List
import logging
from simple_agent.application.file_search import FileSearcher
from simple_agent.infrastructure.textual.autocomplete.domain import (
    Suggestion, CompletionResult, CursorAndLine, FileReference
)
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    Autocompleter, CompletionSearch, NoOpSearch
)

logger = logging.getLogger(__name__)

@dataclass
class FileSuggestion:
    file_path: str
    start_index: int

    @property
    def display_text(self) -> str:
        return self.file_path

    def to_completion_result(self) -> CompletionResult:
         display_marker = f"{FileReference.to_text(self.file_path)} "
         return CompletionResult(
             text=display_marker,
             attachments={self.file_path},
             start_offset=self.start_index
         )

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

class FileSearchAutocompleter:
    def __init__(self, searcher: FileSearcher):
        self.searcher = searcher

    def check(self, cursor_and_line: CursorAndLine) -> CompletionSearch:
        word = cursor_and_line.current_word
        if word.word.startswith("@"):
             return FileSearch(query=word.word[1:], start_index=word.start_index, searcher=self.searcher)
        return NoOpSearch()
