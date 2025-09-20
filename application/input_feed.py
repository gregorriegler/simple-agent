from typing import List


class InputFeed:

    def __init__(self, display):
        self.display = display
        self._stack: List[str] = []

    def stack(self, message: str):
        self._stack.append(message)

    def has_stacked_messages(self) -> bool:
        return bool(self._stack)

    def read(self) -> str:
        if self._stack:
            return self._stack.pop()
        return self.display.input()
