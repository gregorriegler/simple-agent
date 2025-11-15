from __future__ import annotations

import os

from simple_agent.application.ground_rules import GroundRules


class AgentsMdGroundRules(GroundRules):

    def __init__(self, base_dir: str = None, filename: str = "AGENTS.md"):
        self.base_dir = base_dir or os.getcwd()
        self.filename = filename

    def read(self) -> str:
        path = os.path.join(self.base_dir, self.filename)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()
        except FileNotFoundError:
            return ""

