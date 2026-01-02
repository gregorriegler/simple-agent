from typing import List, Optional, Iterator
from dataclasses import dataclass
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteTrigger,
    SuggestionProvider,
    AutocompleteRule,
)
from simple_agent.infrastructure.textual.autocomplete.domain import CursorAndLine, Suggestion

@dataclass
class SingleAutocompleteRule:
    trigger: AutocompleteTrigger
    provider: SuggestionProvider

    def __post_init__(self):
        if self.trigger is None:
            raise ValueError("Trigger cannot be None")
        if self.provider is None:
            raise ValueError("Provider cannot be None")

    async def check(self, cursor_and_line: CursorAndLine) -> List[Suggestion]:
        if self.trigger.is_triggered(cursor_and_line):
            return await self.provider.fetch(cursor_and_line)
        return []

class AutocompleteRules:
    def __init__(self, rules: List[AutocompleteRule] = None):
        self._rules = rules or []

    async def check(self, cursor_and_line: CursorAndLine) -> List[Suggestion]:
        for rule in self._rules:
            suggestions = await rule.check(cursor_and_line)
            if suggestions:
                return suggestions
        return []

    def __iter__(self) -> Iterator[AutocompleteRule]:
        return iter(self._rules)
