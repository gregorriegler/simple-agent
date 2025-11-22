from pathlib import Path

from simple_agent.application.agent_id import AgentId
from simple_agent.application.todo_cleanup import TodoCleanup


class FileSystemTodoCleanup(TodoCleanup):

    def cleanup_all_todos(self) -> None:
        cwd = Path.cwd()
        for file_path in cwd.glob(".*.todos.md"):
            if file_path.is_file():
                file_path.unlink()

        todos_file = cwd / ".todos.md"
        if todos_file.exists() and todos_file.is_file():
            todos_file.unlink()

    def cleanup_todos_for_agent(self, agent_id: AgentId) -> None:
        todo_path = self._todo_path_for_agent(agent_id)
        if todo_path.exists() and todo_path.is_file():
            todo_path.unlink()

    @staticmethod
    def _todo_path_for_agent(agent_id: AgentId) -> Path:
        return Path(f".{agent_id.for_filesystem()}.todos.md")
