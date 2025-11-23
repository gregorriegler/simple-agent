from typing import Mapping, Any

from simple_agent.application.agent_type import AgentType
from simple_agent.infrastructure.model_config import ModelConfig


DEFAULT_STARTING_AGENT_TYPE = "orchestrator"


class UserConfiguration:
    def __init__(self, config: Mapping[str, Any]):
        self._config = config

    def agents_path(self) -> str | None:
        agents_section = self._config.get("agents")
        if isinstance(agents_section, Mapping):
            value = agents_section.get("path")
            if value:
                return str(value)
        return None

    def starting_agent_type(self) -> AgentType:
        agents_section = self._config.get("agents")
        if isinstance(agents_section, Mapping):
            value = agents_section.get("start")
            if value is not None:
                normalized = str(value).strip()
                if normalized:
                    return AgentType(normalized)
        return AgentType(DEFAULT_STARTING_AGENT_TYPE)

    def model_config(self) -> ModelConfig:
        return ModelConfig(self._config)
