from typing import Protocol

from simple_agent.application.tool_library import ToolResult


class Display(Protocol):

    def agent_created(self, event) -> None:
        ...

    def start_session(self, event) -> None:
        ...

    def wait_for_input(self, event) -> None:
        ...

    def assistant_responded(self, event) -> None:
        ...

    def tool_call(self, event) -> None:
        ...

    def tool_result(self, event) -> None:
        ...

    def interrupted(self, event) -> None:
        ...

    def error_occurred(self, event) -> None:
        ...

    def exit(self, event) -> None:
        ...


class AgentDisplay(Protocol):

    def assistant_responded(self, model: str, token_count: int, max_tokens: int) -> None:
        ...

    def tool_call(self, call_id: str, tool) -> None:
        ...

    def tool_result(self, call_id: str, result: ToolResult) -> None:
        ...

    def tool_cancelled(self, call_id: str) -> None:
        ...

    def continue_session(self) -> None:
        ...

    def start_new_session(self) -> None:
        ...

    def waiting_for_input(self) -> None:
        ...

    def interrupted(self) -> None:
        ...

    def error_occurred(self, message) -> None:
        ...

    def exit(self) -> None:
        ...


class DummyDisplay(AgentDisplay):
    def assistant_responded(self, model: str, token_count: int, max_tokens: int) -> None:
        pass
    def tool_call(self, call_id: str, tool) -> None:
        pass
    def tool_result(self, call_id: str, result: ToolResult) -> None:
        pass
    def tool_cancelled(self, call_id: str) -> None:
        pass
    def continue_session(self) -> None:
        pass
    def start_new_session(self) -> None:
        pass
    def waiting_for_input(self) -> None:
        pass
    def interrupted(self) -> None:
        pass
    def error_occurred(self, message) -> None:
        pass
    def exit(self) -> None:
        pass
