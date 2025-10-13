from typing import Protocol

from simple_agent.application.agent import Agent
from simple_agent.application.input import Input


class CreateAgent(Protocol):
    def __call__(
        self,
        agent_id: str,
        user_input: Input,
    ) -> Agent:
        ...
