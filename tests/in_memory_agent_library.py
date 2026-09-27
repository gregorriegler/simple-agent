from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.agent_type import AgentType
from tests.system_prompt_generator_test import GroundRulesStub
from tests.test_helpers import EmbeddedContentStub


class InMemoryAgentLibrary(AgentLibrary):
    def __init__(self, **agent_files: str):
        self._agent_files = agent_files

    def list_agent_types(self) -> list[str]:
        return list(self._agent_files)

    def read_agent_definition(self, agent_type: AgentType) -> AgentDefinition:
        try:
            content = self._agent_files[agent_type.raw]
        except KeyError as error:
            raise FileNotFoundError(
                f"Agent definition '{agent_type.raw}' not found"
            ) from error
        return AgentDefinition(
            agent_type,
            content,
            GroundRulesStub("Test system prompt"),
            EmbeddedContentStub(),
        )

    def starting_agent_id(self) -> AgentId:
        return AgentId(self._starting_agent_definition().agent_name())

    def _starting_agent_definition(self) -> AgentDefinition:
        return self.read_agent_definition(AgentType("agent"))
