from typing import List
import logging
from simple_agent.application.file_search import FileSearcher
from simple_agent.infrastructure.textual.autocomplete.domain import (
    Suggestion, CompletionResult, CursorAndLine, FileReference, FileReferences
)
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteTrigger, SuggestionProvider
)

logger = logging.getLogger(__name__)

class FileSuggestion:
    def __init__(self, file_path: str, start_index: int):
        self.file_path = file_path
        self.start_index = start_index

    @property
    def display_text(self) -> str:
        return self.file_path

    def to_completion_result(self) -> CompletionResult:
         display_marker = f"{FileReference(self.file_path).to_text()} "
         files = FileReferences()
         files.add(self.file_path)
         return CompletionResult(
             text=display_marker,
             files=files,
             start_offset=self.start_index
         )

class AtSymbolTrigger:
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        return cursor_and_line.word.startswith("@")

class FileSearchProvider:
    def __init__(self, searcher: FileSearcher):
        self.searcher = searcher

    async def fetch(self, cursor_and_line: CursorAndLine) -> List[Suggestion]:
        query = cursor_and_line.word[1:] # Strip '@'
        try:
            results = await self.searcher.search(query)
            return [FileSuggestion(str(res), cursor_and_line.word_start_index) for res in results]
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return []
