from simple_agent.infrastructure.textual.autocomplete.domain import (
    Cursor,
    CursorAndLine,
    MessageDraft,
    Suggestion,
    SuggestionList,
    FileReference,
    FileReferences
)
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteTrigger,
    SuggestionProvider,
)
from simple_agent.infrastructure.textual.autocomplete.rules import (
    AutocompleteRule,
    AutocompleteRules
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
