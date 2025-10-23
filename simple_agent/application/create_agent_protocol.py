from typing import Callable, Protocol

from simple_agent.application.agent import Agent
from simple_agent.application.display import Display
from simple_agent.application.input import Input


class AgentFactory(Protocol):
    create_subagent_display: Callable[[str, int], Display]
    create_subagent_input: Callable[[int], Input]

    def __call__(
        self,
        agent_type: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input
    ) -> Agent:
        ...


class SubagentContext:
    def __init__(
        self,
        create_agent: AgentFactory,
        indent_level: int,
        agent_id: str
    ):
        self.create_agent = create_agent
        self.indent_level = indent_level
        self.agent_id = agent_id

    @property
    def create_display(self):
        return self.create_agent.create_subagent_display

    @property
    def create_input(self):
        return self.create_agent.create_subagent_input
