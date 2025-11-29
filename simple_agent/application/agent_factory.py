from typing import Callable

from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId, AgentIdSuffixer
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.events import AgentCreatedEvent, AgentFinishedEvent
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM, Messages
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.application.tool_library_factory import ToolLibraryFactory, ToolContext


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

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def session_storage(self) -> SessionStorage:
        return self._session_storage

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

        tool_context = ToolContext(
            agent_prompt.tool_keys,
            agent_id,
            lambda agent_type, task_description: self.spawn_subagent(
                agent_id, agent_type, task_description, indent_level + 1
            )
        )

        subagent_tools = self._tool_library_factory.create(tool_context)
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

    def create_root_agent(
        self,
        agent_id: AgentId,
        agent_definition,
        user_input: Input,
        persisted_messages
    ) -> Agent:
        tool_context = ToolContext(
            agent_definition.tool_keys(),
            agent_id,
            lambda agent_type, task_description: self.spawn_subagent(
                agent_id, agent_type, task_description, 0
            )
        )
        tools = self._tool_library_factory.create(tool_context)
        tools_documentation = generate_tools_documentation(
            tools.tools, self._agent_library.list_agent_types()
        )
        system_prompt = agent_definition.prompt().render(tools_documentation)
        persisted_messages.seed_system_prompt(system_prompt)

        return Agent(
            agent_id,
            agent_definition.agent_name(),
            tools,
            self._llm,
            user_input,
            self._event_bus,
            self._session_storage,
            persisted_messages
        )

    def spawn_subagent(
        self,
        parent_agent_id: AgentId,
        agent_type: AgentType,
        task_description: str,
        indent_level: int
    ):
        user_input = self._create_subagent_input()
        user_input.stack(task_description)

        subagent = self(
            agent_type,
            parent_agent_id,
            indent_level,
            user_input,
            Messages()
        )

        subagent_id = subagent.agent_id
        self._event_bus.publish(AgentCreatedEvent(parent_agent_id, subagent_id, subagent.agent_name, indent_level))

        try:
            result = subagent.start()
            return result
        finally:
            self._event_bus.publish(AgentFinishedEvent(parent_agent_id, subagent_id))
