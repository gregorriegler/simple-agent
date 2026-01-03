from dataclasses import dataclass
from typing import List, Iterator, Protocol

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


@dataclass
class SingleAutocompleteRule(AutocompleteRule):
    trigger: AutocompleteTrigger
    provider: SuggestionProvider

    def __post_init__(self):
        if self.trigger is None:
            raise ValueError("Trigger cannot be None")
        if self.provider is None:
            raise ValueError("Provider cannot be None")

    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        if self.trigger.is_triggered(cursor_and_line):
            suggestions = await self.provider.fetch(cursor_and_line)
            return SuggestionList(suggestions)
        return SuggestionList([])

class AutocompleteRules(AutocompleteRule):
    def __init__(self, rules: List[AutocompleteRule] = None):
        self._rules = rules or []

    async def suggest(self, cursor_and_line: CursorAndLine) -> SuggestionList:
        for rule in self._rules:
            suggestion_list = await rule.suggest(cursor_and_line)
            if suggestion_list:
                return suggestion_list
        return SuggestionList([])

    def __iter__(self) -> Iterator[AutocompleteRule]:
        return iter(self._rules)
