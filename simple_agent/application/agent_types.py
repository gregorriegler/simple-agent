from typing import List


class AgentTypes:
    def __init__(self, types: List[str]):
        self._types = list(types)

    @staticmethod
    def empty():
        return AgentTypes([])

    def all(self) -> List[str]:
        return self._types

    def __iter__(self):
        return iter(self._types)

    def __bool__(self):
        return bool(self._types)

    def __len__(self):
        return len(self._types)
