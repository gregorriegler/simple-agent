class AgentTypes:
    def __init__(self, types: list[str]):
        self._types = list(types)

    @staticmethod
    def empty():
        return AgentTypes([])

    def all(self) -> list[str]:
        return self._types

    def __iter__(self):
        return iter(self._types)

    def __bool__(self):
        return bool(self._types)

    def __len__(self):
        return len(self._types)
