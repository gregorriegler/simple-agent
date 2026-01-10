import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from simple_agent.application.session_storage import SessionStorage
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

    def session_root(self) -> Path:
        return self._session_root

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
