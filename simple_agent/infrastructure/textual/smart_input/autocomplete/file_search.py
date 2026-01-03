import logging

from simple_agent.application.file_search import FileSearcher
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    CompletionResult, CursorAndLine, FileReference, FileReferences, SuggestionList
)

logger = logging.getLogger(__name__)

class FileSuggestion:
    def __init__(self, file_path: str):
        self.file_path = file_path

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
         )

class AtSymbolTrigger:
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        return cursor_and_line.word.startswith("@")

class FileSearchProvider:
    def __init__(self, searcher: FileSearcher):
        self.searcher = searcher

    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        query = cursor_and_line.word[1:] # Strip '@'
        try:
            results = await self.searcher.search(query)
            return SuggestionList([FileSuggestion(str(res)) for res in results])
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return SuggestionList([])
