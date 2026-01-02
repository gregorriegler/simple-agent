from typing import List, Optional, Iterator
from dataclasses import dataclass
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteTrigger,
    SuggestionProvider,
    AutocompleteRule,
)
from simple_agent.infrastructure.textual.autocomplete.domain import CursorAndLine

@dataclass
class SingleAutocompleteRule:
    trigger: AutocompleteTrigger
    provider: SuggestionProvider

    def check(self, cursor_and_line: CursorAndLine) -> Optional[SuggestionProvider]:
        if self.trigger.is_triggered(cursor_and_line):
            return self.provider
        return None

class AutocompleteRules:
    def __init__(self, rules: List[AutocompleteRule] = None):
        self._rules = rules or []

    def check(self, cursor_and_line: CursorAndLine) -> Optional[SuggestionProvider]:
        for rule in self._rules:
            provider = rule.check(cursor_and_line)
            if provider:
                return provider
        return None

    def __iter__(self) -> Iterator[AutocompleteRule]:
        return iter(self._rules)
