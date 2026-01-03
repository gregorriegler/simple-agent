from dataclasses import dataclass
from typing import List, Iterator, Protocol

from simple_agent.infrastructure.textual.smart_input.autocomplete.domain import Suggestion, CursorAndLine, SuggestionList


class AutocompleteTrigger(Protocol):
    def is_triggered(self, cursor_and_line: CursorAndLine) -> bool:
        ...

class SuggestionProvider(Protocol):
    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        ...

@dataclass
class SingleAutocomplete(SuggestionProvider):
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

class Autocompletes(SuggestionProvider):
    def __init__(self, autocompletes: List[SuggestionProvider] = None):
        self._autocompletes = autocompletes or []

    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        for autocomplete in self._autocompletes:
            suggestion_list = await autocomplete.suggest(cursor_and_line)
            if suggestion_list:
                return suggestion_list
        return SuggestionList([])

    def __iter__(self) -> Iterator[SuggestionProvider]:
        return iter(self._autocompletes)
