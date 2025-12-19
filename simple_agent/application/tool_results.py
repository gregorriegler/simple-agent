from __future__ import annotations

from enum import Enum
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .tool_library import ParsedTool


class ToolResultStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class ToolResult(Protocol):
    @property
    def message(self) -> str:
        ...

    @property
    def success(self) -> bool:
        ...

    @property
    def cancelled(self) -> bool:
        ...

    @property
    def display_title(self) -> str:
        ...

    @property
    def display_body(self) -> str:
        ...

    @property
    def display_language(self) -> str:
        ...

    def __str__(self) -> str:
        ...

    def do_continue(self) -> bool:
        ...


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
        self._entries: list[tuple[ParsedTool, ToolResult]] = []
        self._last_result: ToolResult = SingleToolResult()
        self._cancelled_tool: ParsedTool | None = None

    @property
    def last_result(self) -> ToolResult:
        return self._last_result

    @property
    def message(self) -> str:
        parts = [
            f"Result of {tool}\n{result}"
            for tool, result in self._entries
            if result.do_continue()
        ]
        return "\n\n".join(parts)

    @property
    def success(self) -> bool:
        if self.cancelled:
            return False
        return self._last_result.success

    @property
    def cancelled(self) -> bool:
        return self._cancelled_tool is not None

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

    def add(self, tool: ParsedTool, result: ToolResult) -> None:
        self._entries.append((tool, result))
        self._last_result = result

    def mark_cancelled(self, tool: ParsedTool) -> None:
        self._cancelled_tool = tool

    def cancelled_message(self) -> str:
        if not self._cancelled_tool:
            raise ValueError("cancelled_message called without a cancelled tool")
        return self._cancelled_tool.cancelled_message()
