from typing import Protocol

from simple_agent.application.tool_library import ToolResult


class Display(Protocol):

    def assistant_says(self, message) -> None:
        ...

    def user_says(self, message) -> None:
        ...

    def tool_call(self, tool) -> None:
        ...

    def tool_result(self, result: ToolResult) -> None:
        ...

    def continue_session(self) -> None:
        ...

    def start_new_session(self) -> None:
        ...

    def waiting_for_input(self) -> None:
        ...

    def interrupted(self) -> None:
        ...

    def exit(self) -> None:
        ...


class DummyDisplay:
    def assistant_says(self, message) -> None:
        pass
    def user_says(self, message) -> None:
        pass
    def tool_call(self, tool) -> None:
        pass
    def tool_result(self, result: ToolResult) -> None:
        pass
    def continue_session(self) -> None:
        pass
    def start_new_session(self) -> None:
        pass
    def waiting_for_input(self) -> None:
        pass
    def interrupted(self) -> None:
        pass
    def exit(self) -> None:
        pass
