from typing import Protocol

from simple_agent.application.agent import Agent
from simple_agent.application.input import Input
from simple_agent.application.session_storage import SessionStorage


class AgentFactory(Protocol):
    def __call__(
        self,
        system_prompt_md: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input,
        session_storage: SessionStorage
    ) -> Agent:
        ...


class AgentFactoryRegistry:
    def __init__(self):
        self._factories: dict[str, AgentFactory] = {}

    def register(self, agent_type: str, factory: AgentFactory):
        self._factories[agent_type] = factory

    def get_by_type(self, agent_type: str) -> AgentFactory:
        factory = self._factories.get(agent_type)
        if not factory:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return factory

    def get_available_types(self) -> list[str]:
        return list(self._factories.keys())
