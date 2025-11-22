from __future__ import annotations

from typing import Protocol

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_type import AgentType


class AgentLibrary(Protocol):
    def list_agent_types(self) -> list[str]:
        ...

    def read_agent_definition(self, agent_type: AgentType) -> AgentDefinition:
        ...
