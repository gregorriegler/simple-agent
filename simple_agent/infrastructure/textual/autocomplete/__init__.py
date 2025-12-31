from simple_agent.infrastructure.textual.autocomplete.domain import (
    Word,
    CursorAndLine,
    MessageDraft,
    CompletionResult,
    Suggestion,
    SuggestionList,
    FileReference
)
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteTrigger,
    SuggestionProvider,
    AutocompleteRule,
)
from simple_agent.infrastructure.textual.autocomplete.slash_commands import (
    SlashCommandSuggestion,
    SlashAtStartOfLineTrigger,
    SlashCommandProvider,
)
from simple_agent.infrastructure.textual.autocomplete.file_search import (
    FileSuggestion,
    AtSymbolTrigger,
    FileSearchProvider,
)
