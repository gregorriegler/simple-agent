class AgentId:
    def __init__(self, raw_id: str):
        if not raw_id or not raw_id.strip():
            raise ValueError("Agent ID cannot be empty")
        self._raw_id = raw_id

    def create_subagent_id(self, agent_name: str, instance_counts: dict[str, int]) -> 'AgentId':
        cache_id = f"{self._raw_id}/{agent_name}"
        count = instance_counts.get(cache_id, 0) + 1
        instance_counts[cache_id] = count
        suffix = "" if count == 1 else f"-{count}"
        return AgentId(f"{cache_id}{suffix}")

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
