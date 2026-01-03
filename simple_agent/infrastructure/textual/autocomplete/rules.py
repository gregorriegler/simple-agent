from dataclasses import dataclass
from typing import List, Iterator

from simple_agent.infrastructure.textual.autocomplete.domain import CursorAndLine, SuggestionList
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteTrigger,
    SuggestionProvider,
    AutocompleteRule,
)


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
