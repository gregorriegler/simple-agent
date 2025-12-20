from typing import Mapping, Any

from simple_agent.application.agent_type import AgentType
from simple_agent.infrastructure.model_config import ModelsRegistry


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
        return self.default_starting_agent_type()

    @staticmethod
    def default_starting_agent_type():
        return AgentType(DEFAULT_STARTING_AGENT_TYPE)

    def models_registry(self) -> ModelsRegistry:
        return ModelsRegistry.from_config(self._config)

    def log_level(self) -> str:
        log_section = self._config.get("log")
        if isinstance(log_section, Mapping):
            value = log_section.get("level")
            if value:
                return str(value).upper()
        return "INFO"

    def package_log_levels(self) -> dict[str, str]:
        log_section = self._config.get("log")
        if isinstance(log_section, Mapping):
            packages = log_section.get("packages")
            if isinstance(packages, Mapping):
                return {
                    package: str(level).upper()
                    for package, level in packages.items()
                }
        return {}
