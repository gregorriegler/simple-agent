from typing import List

from .user_input import UserInput


class Input:

    def __init__(self, user_input: UserInput):
        self.user_input = user_input
        self._stack: List[str] = []

    def stack(self, message: str):
        self._stack.append(message)

    def has_stacked_messages(self) -> bool:
        return bool(self._stack)

    def read(self) -> str:
        if self._stack:
            return self._stack.pop()
        return self.user_input.read()

    def escape_requested(self) -> bool:
        return self.user_input.escape_requested()
