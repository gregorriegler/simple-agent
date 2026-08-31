from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Protocol

from .truncation import truncate

if TYPE_CHECKING:
    from .tool_library import RawToolCall, ToolCall


class ToolResultStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class ToolResult(Protocol):
    @property
    def message(self) -> str: ...

    @property
    def success(self) -> bool: ...

    @property
    def cancelled(self) -> bool: ...

    @property
    def display_title(self) -> str: ...

    @property
    def display_body(self) -> str: ...

    @property
    def display_language(self) -> str: ...

    def __str__(self) -> str: ...

    def do_continue(self) -> bool: ...


class SingleToolResult(ToolResult):
    _message: str
    _display_title: str
    _display_body: str
    _display_language: str
    _status: ToolResultStatus
    _completes: bool

    def __init__(
        self,
        message: str = "",
        status: ToolResultStatus = ToolResultStatus.SUCCESS,
        completes: bool = False,
        display_title: str = "",
        display_body: str = "",
        display_language: str = "",
    ):
        self._message = message
        self._display_title = display_title
        self._display_body = display_body
        self._display_language = display_language
        self._completes = completes
        self._status = status

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        return self._message

    @property
    def success(self) -> bool:
        return self._status == ToolResultStatus.SUCCESS

    @property
    def cancelled(self) -> bool:
        return self._status == ToolResultStatus.CANCELLED

    @property
    def display_title(self) -> str:
        return self._display_title

    @property
    def display_body(self) -> str:
        return self._display_body

    @property
    def display_language(self) -> str:
        return self._display_language

    def do_continue(self) -> bool:
        return not self._completes


class ManyToolsResult(ToolResult):
    def __init__(self):
        self._entries: list[tuple[ToolCall, ToolResult]] = []
        self._last_result: ToolResult = SingleToolResult()
        self._cancelled_tool_call: ToolCall | None = None

    @property
    def message(self) -> str:
        parts = [
            f"Result of {tool_call}\n{result}"
            for tool_call, result in self._entries
            if result.do_continue()
        ]
        return "\n\n".join(parts)

    @property
    def tool_results(self) -> list[tuple[RawToolCall, str]]:
        return [
            (tool_call.raw_call, str(result)) for tool_call, result in self._entries
        ]

    @property
    def success(self) -> bool:
        if self.cancelled:
            return False
        return self._last_result.success

    @property
    def cancelled(self) -> bool:
        return self._cancelled_tool_call is not None

    @property
    def display_title(self) -> str:
        return self._last_result.display_title

    @property
    def display_body(self) -> str:
        return self._last_result.display_body

    @property
    def display_language(self) -> str:
        return self._last_result.display_language

    def do_continue(self) -> bool:
        return self._last_result.do_continue()

    def __str__(self) -> str:
        return str(self._last_result)

    def add(self, tool_call: ToolCall, result: ToolResult) -> None:
        self._entries.append((tool_call, result))
        self._last_result = result

    def mark_cancelled(self, tool_call: ToolCall) -> None:
        self._cancelled_tool_call = tool_call


class TruncatedToolResult(ToolResult):
    def __init__(self, result: ToolResult):
        self._result = result

    @property
    def message(self) -> str:
        return truncate(self._result.message)

    @property
    def success(self) -> bool:
        return self._result.success

    @property
    def cancelled(self) -> bool:
        return self._result.cancelled

    @property
    def display_title(self) -> str:
        return self._result.display_title

    @property
    def display_body(self) -> str:
        return truncate(self._result.display_body)

    @property
    def display_language(self) -> str:
        return self._result.display_language

    def do_continue(self) -> bool:
        return self._result.do_continue()

    def __str__(self) -> str:
        return truncate(str(self._result))
