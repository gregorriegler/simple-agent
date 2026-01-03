from typing import Protocol, List

from simple_agent.infrastructure.textual.smart_input.autocomplete.domain import Suggestion, CursorAndLine, SuggestionList


class AutocompleteTrigger(Protocol):
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        ...

class SuggestionProvider(Protocol):
    async def fetch(self, cursor_and_line: CursorAndLine) -> List[Suggestion]:
        ...


class AutocompleteRule(Protocol):
    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        ...
