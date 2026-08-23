import glob
import os

from simple_agent.application.agent_type import AgentType
from simple_agent.application.ground_rules import GroundRules
from simple_agent.application.observer_definition import ObserverDefinition
from simple_agent.infrastructure.agents_md_ground_rules import AgentsMdGroundRules
from simple_agent.infrastructure.user_configuration import UserConfiguration

OBSERVER_SUFFIX = ".observer.md"


class FileSystemObserverLibrary:
    def __init__(self, directory: str, ground_rules: GroundRules | None = None):
        self._directory = directory
        self._ground_rules = ground_rules or AgentsMdGroundRules()

    def list_observers(self) -> list[str]:
        if not os.path.isdir(self._directory):
            return []

        pattern = os.path.join(self._directory, f"*{OBSERVER_SUFFIX}")
        names = [
            os.path.basename(path)[: -len(OBSERVER_SUFFIX)]
            for path in glob.glob(pattern)
        ]
        return sorted(names)

    def read_observer_definition(self, name: str) -> ObserverDefinition:
        path = os.path.join(self._directory, f"{name}{OBSERVER_SUFFIX}")
        try:
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"Observer '{name}' not found in {self._directory}"
            ) from error
        return ObserverDefinition(AgentType(name), content, self._ground_rules)


def create_observer_library(
    user_config: UserConfiguration,
) -> FileSystemObserverLibrary:
    for directory in user_config.agents_candidate_directories():
        library = FileSystemObserverLibrary(directory)
        if library.list_observers():
            return library
    return FileSystemObserverLibrary(user_config.agents_candidate_directories()[0])
