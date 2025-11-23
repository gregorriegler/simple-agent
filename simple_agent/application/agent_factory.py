from typing import Callable

from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId, AgentIdSuffixer
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM, Messages
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.subagent_context import SubagentContext
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.application.tool_library_factory import ToolLibraryFactory


class AgentFactory:
    def __init__(
        self,
        llm: LLM,
        event_bus: EventBus,
        session_storage: SessionStorage,
        tool_library_factory: ToolLibraryFactory,
        agent_library: AgentLibrary,
        create_subagent_input: Callable[[], Input]
    ):
        self._llm = llm
        self._event_bus = event_bus
        self._session_storage = session_storage
        self._tool_library_factory = tool_library_factory
        self._agent_library = agent_library
        self._create_subagent_input = create_subagent_input
        self._agent_suffixer = AgentIdSuffixer()

    def __call__(
        self,
        agent_type: AgentType,
        parent_agent_id: AgentId,
        indent_level: int,
        user_input: Input,
        context: Messages
    ) -> Agent:
        definition = self._agent_library.read_agent_definition(agent_type)
        agent_prompt = definition.load_prompt()
        agent_name = definition.agent_name()
        agent_id = parent_agent_id.create_subagent_id(agent_name, self._agent_suffixer)

        subagent_context = SubagentContext(
            self,
            self._create_subagent_input,
            indent_level + 1,
            agent_id,
            self._event_bus
        )

        subagent_tools = self._tool_library_factory.create(agent_prompt.tool_keys, subagent_context)
        tools_documentation = generate_tools_documentation(subagent_tools.tools, self._agent_library.list_agent_types())
        system_prompt = agent_prompt.render(tools_documentation)

        context.seed_system_prompt(system_prompt)

        return Agent(
            agent_id,
            agent_name,
            subagent_tools,
            self._llm,
            user_input,
            self._event_bus,
            self._session_storage,
            context
        )
