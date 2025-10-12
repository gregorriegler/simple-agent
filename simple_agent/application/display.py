from typing import Protocol


class Display(Protocol):

    def assistant_says(self, message) -> None:
        ...

    def user_says(self, message) -> None:
        ...

    def tool_call(self, tool) -> None:
        ...

    def tool_result(self, result) -> None:
        ...

    def continue_session(self) -> None:
        ...

    def start_new_session(self) -> None:
        ...

    def exit(self) -> None:
        ...
