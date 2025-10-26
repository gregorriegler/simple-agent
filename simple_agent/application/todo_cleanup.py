from typing import Protocol


class TodoCleanup(Protocol):

    def cleanup_all_todos(self) -> None:
        ...

    def cleanup_todos_for_agent(self, agent_id: str) -> None:
        ...


class NoOpTodoCleanup(TodoCleanup):

    def cleanup_all_todos(self) -> None:
        pass

    def cleanup_todos_for_agent(self, agent_id: str) -> None:
        pass
