from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_type import AgentType
from tests.system_prompt_generator_test import GroundRulesStub


class AgentLibraryStub:
    def __init__(
        self,
        observers: list[str] | None = None,
        coding_observers: list[str] | None = None,
    ):
        self._definitions = {
            "agent": AgentDefinition(
                AgentType("agent"),
                f"""---
name: Agent
observers: {observers or []}
---""",
                GroundRulesStub("Test system prompt"),
            ),
            "coding": AgentDefinition(
                AgentType("coding"),
                f"""---
name: Coding
observers: {coding_observers or []}
---""",
                GroundRulesStub("Test system prompt"),
            ),
            "orchestrator": AgentDefinition(
                AgentType("orchestrator"),
                """---
name: Orchestrator
---""",
                GroundRulesStub("Test system prompt"),
            ),
        }

    def list_agent_types(self) -> list[str]:
        return list(self._definitions.keys())

    def read_agent_definition(self, agent_type: AgentType) -> AgentDefinition:
        try:
            return self._definitions[agent_type.raw]
        except KeyError as error:
            raise FileNotFoundError(
                f"Agent definition '{agent_type.raw}' not found"
            ) from error

    def starting_agent_id(self) -> AgentId:
        return AgentId(self._starting_agent_definition().agent_name())

    def _starting_agent_definition(self) -> AgentDefinition:
        return self._definitions["agent"]


class FakeAgentLibrary:
    def __init__(self):
        self._definitions = {
            "agent": AgentDefinition(
                AgentType("agent"), "---\nname: Agent\n---", GroundRulesStub("Prompt")
            ),
        }

    def list_agent_types(self):
        return list(self._definitions.keys())

    def read_agent_definition(self, agent_type):
        return self._definitions[agent_type.raw]

    def starting_agent_id(self):
        return AgentId("Agent")

    def _starting_agent_definition(self):
        return self._definitions["agent"]


class SwitchingAgentLibrary(FakeAgentLibrary):
    def __init__(self):
        super().__init__()
        self._definitions["developer"] = AgentDefinition(
            AgentType("developer"),
            """---\nname: Developer\nmodel: new-model\n---""",
            GroundRulesStub("Prompt"),
        )
