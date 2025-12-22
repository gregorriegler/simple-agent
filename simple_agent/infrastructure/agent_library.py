from __future__ import annotations

import glob
import os
from importlib import resources

from simple_agent.application.agent_type import AgentType
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.ground_rules import GroundRules
from simple_agent.infrastructure.agent_file_conventions import (
    agent_type_from_filename,
    filename_from_agent_type,
)
from simple_agent.infrastructure.agents_md_ground_rules import AgentsMdGroundRules
from simple_agent.application.agent_definition import AgentDefinition


class FileSystemAgentLibrary(AgentLibrary):
    def __init__(self, directory: str):
        self.directory = directory
        self.ground_rules = AgentsMdGroundRules()

    def list_agent_types(self) -> list[str]:
        if not os.path.isdir(self.directory):
            return []

        pattern = os.path.join(self.directory, '*.agent.md')
        agent_types = [
            agent_type_from_filename(os.path.basename(path))
            for path in glob.glob(pattern)
        ]
        return sorted(agent_types)

    def read_agent_definition(self, agent_type: AgentType) -> AgentDefinition:
        filename = filename_from_agent_type(agent_type)
        path = os.path.join(self.directory, filename)
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                content = handle.read()
                return AgentDefinition(agent_type, content, self.ground_rules)
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"Agent definition '{agent_type.raw}' not found in {self.directory}"
            ) from error

    def has_any(self) -> bool:
        return bool(self.list_agent_types())


class BuiltinAgentLibrary:
    def __init__(self, ground_rules: GroundRules = None):
        self.package = 'simple_agent'
        if ground_rules is not None:
            self.ground_rules = ground_rules
        else:
            self.ground_rules = AgentsMdGroundRules()

    def list_agent_types(self) -> list[str]:
        return self._discover_agent_types()

    def read_agent_definition(self, agent_type: AgentType) -> AgentDefinition:
        filename = filename_from_agent_type(agent_type)
        try:
            content = resources.files(self.package).joinpath(filename).read_text(encoding='utf-8')
            return AgentDefinition(agent_type, content, self.ground_rules)
        except (FileNotFoundError, ModuleNotFoundError):
            package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(package_root, filename)
            with open(path, 'r', encoding='utf-8') as handle:
                content = handle.read()
                return AgentDefinition(agent_type, content, self.ground_rules)


    def _discover_agent_types(self) -> list[str]:
        try:
            package_contents = [item.name for item in resources.files(self.package).iterdir()]
            names = [name for name in package_contents if name.endswith('.agent.md')]
        except (FileNotFoundError, ModuleNotFoundError, TypeError):
            names = []

        if names:
            return sorted(agent_type_from_filename(name) for name in names)

        package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pattern = os.path.join(package_root, '*.agent.md')
        names = [os.path.basename(path) for path in glob.glob(pattern)]
        return sorted(agent_type_from_filename(name) for name in names)


def create_agent_library_old(agents_path: str | None, cwd: str) -> AgentLibrary:
    candidate_directories = _candidate_directories(agents_path, cwd)
    return create_agent_library(candidate_directories)


def _candidate_directories(agents_path: str | None, cwd: str) -> list[str]:
    if not agents_path:
        return [os.path.join(cwd, ".simple-agent", "agents")]

    result = os.path.expanduser(agents_path)
    if not os.path.isabs(result):
        result = os.path.abspath(os.path.join(cwd, result))
    return [result]


def create_agent_library(candidate_directories):
    for directory in candidate_directories:
        filesystem_definitions = FileSystemAgentLibrary(directory)
        if filesystem_definitions.has_any():
            return filesystem_definitions
    return BuiltinAgentLibrary()
