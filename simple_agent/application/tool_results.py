from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Protocol

from .truncation import truncate

if TYPE_CHECKING:
    from .tool_library import RawToolCall, ToolInvocation


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
        self._entries: list[tuple[ToolInvocation, ToolResult]] = []
        self._last_result: ToolResult = SingleToolResult()
        self._cancelled: ToolInvocation | None = None

    @property
    def message(self) -> str:
        return self._last_result.message

    @property
    def tool_results(self) -> list[tuple[RawToolCall, str]]:
        return [(invocation.call, str(result)) for invocation, result in self._entries]

    @property
    def success(self) -> bool:
        if self.cancelled:
            return False
        return self._last_result.success

    @property
    def cancelled(self) -> bool:
        return self._cancelled is not None

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

    def add(self, invocation: ToolInvocation, result: ToolResult) -> None:
        self._entries.append((invocation, result))
        self._last_result = result

    def mark_cancelled(self, invocation: ToolInvocation) -> None:
        self._cancelled = invocation


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
