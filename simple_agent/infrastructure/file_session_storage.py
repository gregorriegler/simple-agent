import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from simple_agent.application.agent_id import AgentId
from simple_agent.application.llm import Messages
from simple_agent.application.session_storage import AgentMetadata, SessionStorage
from simple_agent.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SessionMetadata:
    session_id: str
    created_at: str
    cwd: str


class FileSessionStorage(SessionStorage):
    def __init__(self, base_dir: Path, session_root: Path, metadata: SessionMetadata):
        self._base_dir = base_dir
        self._session_root = session_root
        self._metadata = metadata
        (self._session_root / "agents").mkdir(parents=True, exist_ok=True)
        self._ensure_manifest()

    @classmethod
    def create(cls, base_dir: Path, continue_session: bool, cwd: Path):
        base_dir.mkdir(parents=True, exist_ok=True)
        session_root = cls._latest_session_dir(base_dir) if continue_session else None
        if session_root is None:
            session_root = base_dir / cls._new_session_id()
        metadata = SessionMetadata(
            session_id=session_root.name,
            created_at=cls._current_timestamp(),
            cwd=str(cwd),
        )
        return cls(base_dir, session_root, metadata)

    def load_messages(self, agent_id: AgentId) -> Messages:
        path = self._messages_path(agent_id)
        if not path.exists():
            return Messages()
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            logger.warning("Could not load session file %s: %s", path, error)
            return Messages()
        except Exception as error:
            logger.warning("Could not load session file %s: %s", path, error)
            return Messages()
        if isinstance(raw_data, list):
            return Messages(raw_data)
        return Messages()

    def save_messages(self, agent_id: AgentId, messages: Messages) -> None:
        path = self._messages_path(agent_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps(messages.to_list(), indent=2), encoding="utf-8")
        except Exception as error:
            logger.warning("Could not save session file %s: %s", path, error)

    def session_root(self) -> Path:
        return self._session_root

    def list_stored_agents(self) -> list[AgentId]:
        agents_dir = self._session_root / "agents"
        if not agents_dir.exists():
            return []
        agent_ids = []
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and (agent_dir / "messages.json").exists():
                raw_id = agent_dir.name.replace("-", "/")
                agent_ids.append(AgentId(raw_id, root=self._session_root))
        return sorted(agent_ids, key=lambda a: a.depth())

    def load_metadata(self, agent_id: AgentId) -> AgentMetadata:
        path = self._metadata_path(agent_id)
        if not path.exists():
            return AgentMetadata()
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
            return AgentMetadata(
                model=raw_data.get("model", ""),
                max_tokens=raw_data.get("max_tokens", 0),
                input_tokens=raw_data.get("input_tokens", 0),
            )
        except (json.JSONDecodeError, Exception) as error:
            logger.warning("Could not load metadata file %s: %s", path, error)
            return AgentMetadata()

    def save_metadata(self, agent_id: AgentId, metadata: AgentMetadata) -> None:
        path = self._metadata_path(agent_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(
                json.dumps(
                    {
                        "model": metadata.model,
                        "max_tokens": metadata.max_tokens,
                        "input_tokens": metadata.input_tokens,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as error:
            logger.warning("Could not save metadata file %s: %s", path, error)

    def _messages_path(self, agent_id: AgentId) -> Path:
        return (
            self._session_root / "agents" / agent_id.for_filesystem() / "messages.json"
        )

    def _metadata_path(self, agent_id: AgentId) -> Path:
        return (
            self._session_root / "agents" / agent_id.for_filesystem() / "metadata.json"
        )

    def _ensure_manifest(self) -> None:
        manifest_path = self._session_root / "manifest.json"
        if manifest_path.exists():
            return
        self._session_root.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "session_id": self._metadata.session_id,
                    "created_at": self._metadata.created_at,
                    "cwd": self._metadata.cwd,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _latest_session_dir(base_dir: Path) -> Path | None:
        candidates = [path for path in base_dir.iterdir() if path.is_dir()]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)

    @staticmethod
    def _new_session_id() -> str:
        return f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now(UTC).isoformat()
