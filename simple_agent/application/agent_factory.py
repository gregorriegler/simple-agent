from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId, AgentIdSuffixer
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM, Messages
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.application.tool_library_factory import ToolLibraryFactory, ToolContext
from simple_agent.application.user_input import UserInput


class AgentFactory:
    def __init__(
        self,
        llm: LLM,
        event_bus: EventBus,
        session_storage: SessionStorage,
        tool_library_factory: ToolLibraryFactory,
        agent_library: AgentLibrary,
        user_input: UserInput
    ):
        self._llm = llm
        self._event_bus = event_bus
        self._session_storage = session_storage
        self._tool_library_factory = tool_library_factory
        self._agent_library = agent_library
        self._user_input = user_input
        self._agent_suffixer = AgentIdSuffixer()

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def session_storage(self) -> SessionStorage:
        return self._session_storage

    def create_input(self, initial_message: str | None = None) -> Input:
        inp = Input(self._user_input)
        if initial_message:
            inp.stack(initial_message)
        return inp

    def create_spawner(self, parent_agent_id: AgentId) -> SubagentSpawner:
        def spawn(agent_type, task_description):
            subagent = self.create_subagent(
                agent_type, parent_agent_id, task_description, Messages()
            )
            return subagent.start()
        return spawn

    def create_subagent(
        self,
        agent_type: AgentType,
        parent_agent_id: AgentId,
        initial_message: str | None,
        context: Messages
    ) -> Agent:
        definition = self._agent_library.read_agent_definition(agent_type)
        agent_prompt = definition.load_prompt()
        agent_name = definition.agent_name()
        agent_id = parent_agent_id.create_subagent_id(agent_name, self._agent_suffixer)

        tool_context = ToolContext(
            agent_prompt.tool_keys,
            agent_id
        )
        spawner = self.create_spawner(agent_id)

        subagent_tools = self._tool_library_factory.create(tool_context, spawner)
        tools_documentation = generate_tools_documentation(subagent_tools.tools, self._agent_library.list_agent_types())
        system_prompt = agent_prompt.render(tools_documentation)

        context.seed_system_prompt(system_prompt)

        return Agent(
            agent_id,
            agent_name,
            subagent_tools,
            self._llm,
            self.create_input(initial_message),
            self._event_bus,
            self._session_storage,
            context,
        )

    def create_root_agent(
        self,
        agent_id: AgentId,
        agent_definition,
        initial_message: str | None,
        persisted_messages
    ) -> Agent:
        tool_context = ToolContext(
            agent_definition.tool_keys(),
            agent_id
        )
        spawner = self.create_spawner(agent_id)
        tools = self._tool_library_factory.create(tool_context, spawner)
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
            self.create_input(initial_message),
            self._event_bus,
            self._session_storage,
            persisted_messages
        )
