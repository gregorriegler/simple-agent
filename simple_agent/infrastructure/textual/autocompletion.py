from typing import Protocol, List, Any, Optional
from dataclasses import dataclass, field
import logging

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.file_search import FileSearcher

logger = logging.getLogger(__name__)

@dataclass
class AutocompleteRequest:
    query: str
    start_index: int
    trigger_char: str

@dataclass
class CompletionResult:
    text: str
    attachments: set[str] = field(default_factory=set)
    start_offset: Optional[int] = None

class Autocompleter(Protocol):
    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteRequest]:
        """
        Check if autocomplete should be triggered.
        Returns request if triggered, None otherwise.
        """
        ...

    async def get_suggestions(self, request: AutocompleteRequest) -> List[Any]:
        """
        Get list of suggestions based on request.
        """
        ...

    def format_suggestion(self, suggestion: Any) -> str:
        """
        Format a suggestion for display in the popup.
        """
        ...

    def get_completion(self, suggestion: Any) -> CompletionResult:
        """
        Get the completion result (text to insert and attachments) for a selected suggestion.
        """
        ...


class SlashCommandAutocompleter:
    def __init__(self, registry: SlashCommandRegistry):
        self.registry = registry

    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteRequest]:
        if row == 0 and col > 0 and line.startswith("/") and " " not in line[:col]:
            return AutocompleteRequest(query=line[:col], start_index=0, trigger_char="/")
        return None

    async def get_suggestions(self, request: AutocompleteRequest) -> List[Any]:
        return self.registry.get_matching_commands(request.query)

    def format_suggestion(self, suggestion: Any) -> str:
        return f"{suggestion.name} - {suggestion.description}"

    def get_completion(self, suggestion: Any) -> CompletionResult:
        cmd_name = suggestion.name
        return CompletionResult(text=cmd_name + " ")


class FileSearchAutocompleter:
    def __init__(self, searcher: FileSearcher):
        self.searcher = searcher

    def check(self, row: int, col: int, line: str) -> Optional[AutocompleteRequest]:
        # Check for file search (@)
        text_before_cursor = line[:col]

        # Find the start of the word before cursor
        last_space_index = text_before_cursor.rfind(" ")
        word_start_index = last_space_index + 1
        current_word = text_before_cursor[word_start_index:]

        if current_word.startswith("@"):
             return AutocompleteRequest(query=current_word[1:], start_index=word_start_index, trigger_char="@")
        return None

    async def get_suggestions(self, request: AutocompleteRequest) -> List[Any]:
        try:
            return await self.searcher.search(request.query)
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return []

    def format_suggestion(self, suggestion: Any) -> str:
        return str(suggestion)

    def get_completion(self, suggestion: Any) -> CompletionResult:
        file_path = str(suggestion)
        display_marker = f"[📦{file_path}] "
        return CompletionResult(text=display_marker, attachments={file_path})
