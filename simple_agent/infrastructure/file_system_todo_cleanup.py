from pathlib import Path

from simple_agent.application.agent_id import AgentId
from simple_agent.application.todo_cleanup import TodoCleanup


class FileSystemTodoCleanup(TodoCleanup):
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path.cwd()

    def cleanup_all_todos(self) -> None:
        for file_path in self._root.glob(".*.todos.md"):
            if file_path.is_file():
                file_path.unlink()

        todos_file = self._root / ".todos.md"
        if todos_file.exists() and todos_file.is_file():
            todos_file.unlink()

    def cleanup_todos_for_agent(self, agent_id: AgentId) -> None:
        todo_path = self._todo_path_for_agent(agent_id)
        if todo_path.exists() and todo_path.is_file():
            todo_path.unlink()

    @staticmethod
    def _todo_path_for_agent(agent_id: AgentId) -> Path:
        return Path(agent_id.todo_filename())
