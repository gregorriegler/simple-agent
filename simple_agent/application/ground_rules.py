from __future__ import annotations

from typing import Protocol


class GroundRules(Protocol):
    def read(self) -> str: ...
