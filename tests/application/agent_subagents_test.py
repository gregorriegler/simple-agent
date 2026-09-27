from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.event_store import NoOpEventStore
from simple_agent.application.inboxes import AgentInboxes
from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.infrastructure.file_intents import FileIntents
from simple_agent.infrastructure.file_todos import FileTodos
from simple_agent.tools.all_tools import AllToolsFactory
from tests.in_memory_agent_library import InMemoryAgentLibrary
from tests.test_helpers import DummyProjectTree


def test_an_agent_with_an_empty_subagents_list_is_offered_no_subagents():
    agents = InMemoryAgentLibrary(
        router="""---
tools: subagent
subagents: []
---""",
        coding="",
    )

    expected = """\
tools: subagent
agenttype: Type of agent to create."""
    assert what_agent_sees("router", agents) == expected


class RecordingLLMProvider:
    def __init__(self):
        self._llm = create_llm_stub([])
        self.tools: list = []

    def get(self, model_name: str | None = None, tools: list | None = None):
        self.tools = tools or []
        return self._llm

    def get_available_models(self) -> list[str]:
        return [self._llm.model]


def what_agent_sees(agent_type: str, agents: InMemoryAgentLibrary) -> str:
    llm_provider = RecordingLLMProvider()
    factory = AgentFactory(
        event_bus=SimpleEventBus(),
        tool_library_factory=AllToolsFactory(FileIntents(), FileTodos()),
        agent_library=agents,
        inboxes=AgentInboxes(),
        llm_provider=llm_provider,
        project_tree=DummyProjectTree(),
        event_store=NoOpEventStore(),
        agent_task_manager=AgentTaskManager(),
    )
    agent_id = AgentId(agent_type)
    factory.build_brain(agent_id, AgentType(agent_type), factory.create_inbox(agent_id))
    return print_view(llm_provider.tools)


def print_view(tools: list) -> str:
    tool_names = ", ".join(tool.name for tool in tools)
    agenttype = [
        argument.description
        for tool in tools
        for argument in tool.arguments.header
        if argument.name == "agenttype"
    ]
    return f"tools: {tool_names}\nagenttype: {''.join(agenttype)}"
