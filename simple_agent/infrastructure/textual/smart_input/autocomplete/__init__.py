from simple_agent.infrastructure.textual.smart_input.autocomplete.domain import (
    Cursor,
    CursorAndLine,
    CompletionResult,
    Suggestion,
    SuggestionList,
    FileReference,
    FileReferences
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.protocols import (
    AutocompleteTrigger,
    SuggestionProvider,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.rules import (
    AutocompleteRule,
    AutocompleteRules
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.slash_commands import (
    SlashCommandSuggestion,
    SlashAtStartOfLineTrigger,
    SlashCommandProvider,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.file_search import (
    FileSuggestion,
    AtSymbolTrigger,
    FileSearchProvider,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.popup import (
    AutocompletePopup,
    PopupAnchor,
    PopupLayout,
)
