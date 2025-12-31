from simple_agent.infrastructure.textual.autocomplete.domain import (
    WordAtCursor,
    CursorAndLine,
    MessageDraft,
    CompletionResult,
    Suggestion,
    SuggestionList,
    FileReference
)
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    CompletionSearch,
    Autocompleter,
    NoOpSearch,
)
from simple_agent.infrastructure.textual.autocomplete.slash_commands import (
    SlashCommandSuggestion,
    SlashCommandSearch,
    SlashCommandAutocompleter,
)
from simple_agent.infrastructure.textual.autocomplete.file_search import (
    FileSuggestion,
    FileSearch,
    FileSearchAutocompleter,
)
from simple_agent.infrastructure.textual.autocomplete.engines import (
    CompositeAutocompleter,
    NullAutocompleter,
)
