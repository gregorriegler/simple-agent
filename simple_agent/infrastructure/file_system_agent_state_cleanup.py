from pathlib import Path

from simple_agent.application.agent_id import AgentId, state_file_globs
from simple_agent.application.agent_state_cleanup import AgentStateCleanup

LEGACY_SHARED_TODO_FILE = ".todos.md"


class FileSystemAgentStateCleanup(AgentStateCleanup):
    def __init__(self, root: Path) -> None:
        self._root = root

    def cleanup_all(self) -> None:
        for pattern in state_file_globs():
            for file_path in self._root.glob(pattern):
                self._delete(file_path)
        self._delete(self._root / LEGACY_SHARED_TODO_FILE)

    def cleanup_for_agent(self, agent_id: AgentId) -> None:
        for path in agent_id.state_filenames():
            self._delete(path)

    @staticmethod
    def _delete(path: Path) -> None:
        if path.exists() and path.is_file():
            path.unlink()
