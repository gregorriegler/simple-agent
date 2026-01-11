from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId, AgentIdSuffixer
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.agent_type import AgentType
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.event_bus import EventBus
from simple_agent.application.event_store import EventStore
from simple_agent.application.events_to_messages import events_to_messages
from simple_agent.application.input import Input
from simple_agent.application.llm import LLMProvider, Messages
from simple_agent.application.project_tree import ProjectTree
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.application.tool_library_factory import (
    ToolContext,
    ToolLibraryFactory,
)
from simple_agent.application.user_input import UserInput


class AgentFactory:
    def __init__(
        self,
        event_bus: EventBus,
        tool_library_factory: ToolLibraryFactory,
        agent_library: AgentLibrary,
        user_input: UserInput,
        llm_provider: LLMProvider,
        project_tree: ProjectTree,
        event_store: EventStore | None = None,
    ):
        self._event_bus = event_bus
        self._tool_library_factory = tool_library_factory
        self._agent_library = agent_library
        self._user_input = user_input
        self._agent_suffixer = AgentIdSuffixer()
        self._llm_provider = llm_provider
        self._project_tree = project_tree
        self._event_store = event_store

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    def create_input(self, initial_message: str | None = None) -> Input:
        inp = Input(self._user_input)
        if initial_message:
            inp.stack(initial_message)
        return inp

    def create_spawner(self, parent_agent_id: AgentId) -> SubagentSpawner:
        async def spawn(agent_type, task_description):
            definition = self._agent_library.read_agent_definition(agent_type)
            agent_id = parent_agent_id.create_subagent_id(
                definition.agent_name(), self._agent_suffixer
            )
            if self._event_store:
                events = self._event_store.load_events(agent_id)
                context = events_to_messages(events, agent_id)
            else:
                context = Messages()

            subagent = self.create_agent(
                agent_id, definition, task_description, context, agent_type
            )
            return await subagent.start()

        return spawn

    def create_agent_from_history(self, agent_id: AgentId, agent_type: str) -> Agent:
        definition = self._agent_library.read_agent_definition(AgentType(agent_type))
        if self._event_store:
            events = self._event_store.load_events(agent_id)
            context = events_to_messages(events, agent_id)
        else:
            context = Messages()

        return self.create_agent(agent_id, definition, None, context, agent_type)

    def create_agent(
        self,
        agent_id: AgentId,
        definition,
        initial_message: str | None,
        messages: Messages,
        agent_type: str = "",
    ) -> Agent:
        tool_context = ToolContext(definition.tool_keys(), agent_id)
        spawner = self.create_spawner(agent_id)
        tools = self._tool_library_factory.create(
            tool_context, spawner, AgentTypes(self._agent_library.list_agent_types())
        )
        tools_documentation = generate_tools_documentation(
            tools.tools, tools.tool_syntax
        )
        system_prompt = definition.prompt().render(
            tools_documentation, self._project_tree
        )
        messages.seed_system_prompt(system_prompt)

        return Agent(
            agent_id,
            definition.agent_name(),
            tools,
            self._llm_provider,
            definition.model(),
            self.create_input(initial_message),
            self._event_bus,
            messages,
            agent_type=agent_type,
        )
