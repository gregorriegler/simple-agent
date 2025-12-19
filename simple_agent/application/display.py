from typing import Protocol

class Display(Protocol):

    def agent_created(self, event) -> None:
        ...

    def exit(self, event) -> None:
        ...


class AgentDisplay(Protocol):

    def exit(self) -> None:
        ...
