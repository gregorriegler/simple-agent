from typing import Protocol, List
from simple_agent.infrastructure.textual.autocomplete.domain import Suggestion, CursorAndLine

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

class NoOpSearch:
    async def get_suggestions(self) -> List[Suggestion]:
        return []

    def is_triggered(self) -> bool:
        return False
