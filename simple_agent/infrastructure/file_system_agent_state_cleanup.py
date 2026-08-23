from pathlib import Path

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_state_cleanup import AgentStateCleanup

STATE_FILE_SUFFIXES = ("todos.md", "intent.md")
LEGACY_SHARED_TODO_FILE = ".todos.md"


class FileSystemAgentStateCleanup(AgentStateCleanup):
    def __init__(self, root: Path) -> None:
        self._root = root

    def cleanup_all(self) -> None:
        for suffix in STATE_FILE_SUFFIXES:
            for file_path in self._root.glob(f".*.{suffix}"):
                self._delete(file_path)
        self._delete(self._root / LEGACY_SHARED_TODO_FILE)

    def cleanup_for_agent(self, agent_id: AgentId) -> None:
        self._delete(Path(agent_id.todo_filename()))
        self._delete(Path(agent_id.intent_filename()))

    @staticmethod
    def _delete(path: Path) -> None:
        if path.exists() and path.is_file():
            path.unlink()
