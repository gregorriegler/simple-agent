from pathlib import Path

class AgentId:
    def __init__(self, raw_id: str, root: Path | None = None):
        if not raw_id or not raw_id.strip():
            raise ValueError("Agent ID cannot be empty")
        self._raw_id = raw_id
        self._root = root

    def with_root(self, root: Path) -> 'AgentId':
        return AgentId(self._raw_id, root=root)

    def with_suffix(self, suffix: str) -> 'AgentId':
        if suffix:
            return AgentId(f"{self._raw_id}{suffix}", root=self._root)
        return self

    def create_subagent_id(self, agent_name: str, suffixer: 'AgentIdSuffixer') -> 'AgentId':
        base_id = AgentId(f"{self._raw_id}/{agent_name}", root=self._root)
        suffix = suffixer.suffix(base_id)
        return base_id.with_suffix(suffix)

    def has_parent(self) -> bool:
        return "/" in self._raw_id

    def parent(self) -> 'AgentId | None':
        if "/" not in self._raw_id:
            return None
        parent_raw = self._raw_id.rsplit("/", 1)[0]
        return AgentId(parent_raw, root=self._root)

    def depth(self) -> int:
        return self._raw_id.count("/")

    @property
    def raw(self) -> str:
        return self._raw_id

    def for_filesystem(self) -> str:
        return self._raw_id.replace("/", "-").replace("\\", "-").replace(" ", "-")

    def todo_filename(self) -> Path:
        root = self._root or Path(".")
        return root / f".{self.for_filesystem()}.todos.md"

    def for_ui(self) -> str:
        return self.for_filesystem()

    def __str__(self) -> str:
        return self._raw_id

    def __repr__(self) -> str:
        return f"AgentId('{self._raw_id}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, AgentId):
            return self._raw_id == other._raw_id
        return False

    def __hash__(self) -> int:
        return hash(self._raw_id)

class AgentIdSuffixer:
    def __init__(self):
        self._counts: dict[AgentId, int] = {}

    def suffix(self, base_id: AgentId) -> str:
        count = self._counts.get(base_id, 0) + 1
        self._counts[base_id] = count
        return "" if count == 1 else f"-{count}"
