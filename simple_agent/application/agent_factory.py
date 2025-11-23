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
from simple_agent.application.tool_library_factory import ToolLibraryFactory


class SubagentContext:

    def __init__(
        self,
        agent_factory: "AgentFactory",
        create_subagent_input,
        indent_level: int,
        agent_id: AgentId,
        event_bus: EventBus
    ):
        self.agent_factory = agent_factory
        self.create_input = create_subagent_input
        self.indent_level = indent_level
        self.agent_id = agent_id
        self._event_bus = event_bus

    def notify_subagent_created(self, subagent_id: AgentId, subagent_name: str) -> None:
        self._event_bus.publish(AgentCreatedEvent(self.agent_id, subagent_id, subagent_name, self.indent_level))

    def notify_subagent_finished(self, subagent_id: AgentId) -> None:
        self._event_bus.publish(AgentFinishedEvent(self.agent_id, subagent_id))

    def spawn_subagent(self, agent_type: AgentType, task_description: str):
        user_input = self.create_input()
        user_input.stack(task_description)

        subagent = self.agent_factory(
            agent_type,
            self.agent_id,
            self.indent_level,
            user_input,
            Messages()
        )

        self.notify_subagent_created(subagent.agent_id, subagent.agent_name)

        try:
            result = subagent.start()
            return result
        finally:
            self.notify_subagent_finished(subagent.agent_id)


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
