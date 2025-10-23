from typing import Callable, Any

from simple_agent.application.agent_factory import CreateAgent
from simple_agent.application.input import Input


class SubagentContext:
    def __init__(
        self,
        create_agent: CreateAgent | None,
        create_display: Callable[[str, int], Any],
        create_input: Callable[[int], Input],
        indent_level: int,
        agent_id: str
    ):
        self.create_agent = create_agent
        self.create_display = create_display
        self.create_input = create_input
        self.indent_level = indent_level
        self.agent_id = agent_id
