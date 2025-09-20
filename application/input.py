from typing import Callable, List, Optional


class Input:

    def __init__(self, display, escape_detector: Optional[Callable[[], bool]] = None):
        self.display = display
        self._stack: List[str] = []
        self._escape_detector = escape_detector

    def stack(self, message: str):
        self._stack.append(message)

    def has_stacked_messages(self) -> bool:
        return bool(self._stack)

    def read(self) -> str:
        if self._stack:
            return self._stack.pop()
        return self.display.input()

    def escape_requested(self) -> bool:
        if self._escape_detector is None:
            return False
        return self._escape_detector()

    def set_escape_detector(self, escape_detector: Callable[[], bool]):
        self._escape_detector = escape_detector
