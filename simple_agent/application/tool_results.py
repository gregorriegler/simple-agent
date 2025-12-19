from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass(init=False)
class SingleToolResult(ToolResult):
    message: str = field(default="")
    display_title: str = field(default="")
    display_body: str = field(default="")
    display_language: str = field(default="")
    _status: ToolResultStatus = field(init=False, repr=False)

    def __init__(
        self,
        message: str = "",
        success: bool = True,
        cancelled: bool = False,
        display_title: str = "",
        display_body: str = "",
        display_language: str = "",
    ):
        if cancelled and success:
            raise ValueError("ToolResult cannot be both success and cancelled")
        self.message = message
        self.display_title = display_title
        self.display_body = display_body
        self.display_language = display_language
        if cancelled:
            self._status = ToolResultStatus.CANCELLED
        elif success:
            self._status = ToolResultStatus.SUCCESS
        else:
            self._status = ToolResultStatus.FAILURE

    def __str__(self) -> str:
        return self.message

    @property
    def success(self) -> bool:
        return self._status == ToolResultStatus.SUCCESS

    @property
    def cancelled(self) -> bool:
        return self._status == ToolResultStatus.CANCELLED

    def do_continue(self) -> bool:
        raise NotImplementedError


@dataclass(init=False)
class ContinueResult(SingleToolResult):
    def do_continue(self) -> bool:
        return True


@dataclass(init=False)
class CompleteResult(SingleToolResult):
    def do_continue(self) -> bool:
        return False


class ManyToolsResult(ToolResult):
    def __init__(self):
        self._entries: list[tuple[ParsedTool, ToolResult]] = []
        self._last_result: ToolResult = ContinueResult()
        self._cancelled_tool: ParsedTool | None = None

    @property
    def last_result(self) -> ToolResult:
        return self._last_result

    @property
    def message(self) -> str:
        return self._last_result.message

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

    def format_continue_message(self) -> str | None:
        parts = [
            f"Result of {tool}\n{result}"
            for tool, result in self._entries
            if isinstance(result, ContinueResult)
        ]
        return "\n\n".join(parts) if parts else None

    def has_continue_results(self) -> bool:
        return any(isinstance(result, ContinueResult) for _, result in self._entries)

    def mark_cancelled(self, tool: ParsedTool) -> None:
        self._cancelled_tool = tool

    def was_cancelled(self) -> bool:
        return self._cancelled_tool is not None

    def cancelled_message(self) -> str:
        if not self._cancelled_tool:
            raise ValueError("cancelled_message called without a cancelled tool")
        return self._cancelled_tool.cancelled_message()
