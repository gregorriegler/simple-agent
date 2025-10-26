from typing import Protocol


class TodoCleanup(Protocol):

    def cleanup_all_todos(self) -> None:
        ...


class NoOpTodoCleanup(TodoCleanup):

    def cleanup_all_todos(self) -> None:
        pass
