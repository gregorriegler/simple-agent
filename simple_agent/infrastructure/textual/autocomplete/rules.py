from typing import List, Optional, Iterator
from dataclasses import dataclass
from simple_agent.infrastructure.textual.autocomplete.protocols import AutocompleteTrigger, SuggestionProvider
from simple_agent.infrastructure.textual.autocomplete.domain import CursorAndLine

@dataclass
class AutocompleteRule:
    trigger: AutocompleteTrigger
    provider: SuggestionProvider

class AutocompleteRules:
    def __init__(self, rules: List[AutocompleteRule] = None):
        self._rules = rules or []

    def find_triggered(self, cursor_and_line: CursorAndLine) -> Optional[AutocompleteRule]:
        for rule in self._rules:
            if rule.trigger.is_triggered(cursor_and_line):
                return rule
        return None

    def __iter__(self) -> Iterator[AutocompleteRule]:
        return iter(self._rules)
