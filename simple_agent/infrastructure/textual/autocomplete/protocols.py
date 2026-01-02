from typing import Protocol, List, Optional
from dataclasses import dataclass
from simple_agent.infrastructure.textual.autocomplete.domain import Suggestion, CursorAndLine

class AutocompleteTrigger(Protocol):
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        """
        Pure logic. Determines if the autocomplete process should start.
        """
        ...

class SuggestionProvider(Protocol):
    async def fetch(self, cursor_and_line: CursorAndLine) -> List[Suggestion]:
        """
        Pure data. Fetches items when requested.
        """
        ...


class AutocompleteRule(Protocol):
    async def check(self, cursor_and_line: CursorAndLine) -> List[Suggestion]:
        """
        Checks if the rule is triggered and returns suggestions if so.
        """
        ...
