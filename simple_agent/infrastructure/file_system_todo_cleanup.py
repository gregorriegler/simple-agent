from pathlib import Path

from simple_agent.application.todo_cleanup import TodoCleanup


class FileSystemTodoCleanup(TodoCleanup):

    def cleanup_all_todos(self) -> None:
        cwd = Path.cwd()
        for file_path in cwd.glob(".*.todos.md"):
            if file_path.is_file():
                file_path.unlink()
