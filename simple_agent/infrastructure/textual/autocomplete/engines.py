from typing import List
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    Autocompleter,
    CompletionSearch,
    NoOpSearch
)
from simple_agent.infrastructure.textual.autocomplete.domain import CursorAndLine

class CompositeAutocompleter:
    def __init__(self, autocompleters: List[Autocompleter]):
        self.autocompleters = autocompleters

    def check(self, cursor_and_line: CursorAndLine) -> CompletionSearch:
        for autocompleter in self.autocompleters:
            search = autocompleter.check(cursor_and_line)
            if search.is_triggered():
                return search
        return NoOpSearch()

class NullAutocompleter:
    def check(self, cursor_and_line: CursorAndLine) -> CompletionSearch:
        return NoOpSearch()
