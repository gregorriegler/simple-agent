class AgentId:
    def __init__(self, raw_id: str):
        if not raw_id or not raw_id.strip():
            raise ValueError("Agent ID cannot be empty")
        self._raw_id = raw_id

    def with_suffix(self, suffix: str) -> 'AgentId':
        if suffix:
            return AgentId(f"{self._raw_id}{suffix}")
        return self

    def create_subagent_id(self, agent_name: str, suffixer: 'AgentIdSuffixer') -> 'AgentId':
        base_id = AgentId(f"{self._raw_id}/{agent_name}")
        suffix = suffixer.suffix(base_id)
        return base_id.with_suffix(suffix)

    @property
    def raw(self) -> str:
        return self._raw_id

    def for_filesystem(self) -> str:
        return self._raw_id.replace("/", "-").replace("\\", "-").replace(" ", "-")

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
