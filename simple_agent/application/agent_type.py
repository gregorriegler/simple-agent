class AgentType:
    def __init__(self, type_name: str):
        if not type_name or not type_name.strip():
            raise ValueError("Agent type cannot be empty")
        self._type_name = type_name

    @property
    def raw(self) -> str:
        return self._type_name

    def __str__(self) -> str:
        return self._type_name

    def __repr__(self) -> str:
        return f"AgentType('{self._type_name}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, AgentType):
            return self._type_name == other._type_name
        return False

    def __hash__(self) -> int:
        return hash(self._type_name)
