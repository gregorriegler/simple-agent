from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId, AgentIdSuffixer
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLMProvider, Messages
from simple_agent.application.project_tree import ProjectTree
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.application.tool_library_factory import ToolLibraryFactory, ToolContext
from simple_agent.application.user_input import UserInput




class AgentFactory:
    def __init__(
        self,
        event_bus: EventBus,
        session_storage: SessionStorage,
        tool_library_factory: ToolLibraryFactory,
        agent_library: AgentLibrary,
        user_input: UserInput,
        llm_provider: LLMProvider,
        project_tree: ProjectTree,
    ):
        self._event_bus = event_bus
        self._session_storage = session_storage
        self._tool_library_factory = tool_library_factory
        self._agent_library = agent_library
        self._user_input = user_input
        self._agent_suffixer = AgentIdSuffixer()
        self._llm_provider = llm_provider
        self._project_tree = project_tree

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
        async def spawn(agent_type, task_description):
            definition = self._agent_library.read_agent_definition(agent_type)
            agent_id = parent_agent_id.create_subagent_id(
                definition.agent_name(), self._agent_suffixer
            )
            subagent = self.create_agent(
                agent_id, definition, task_description, Messages()
            )
            return await subagent.start()
        return spawn

    def create_agent(
        self,
        agent_id: AgentId,
        definition,
        initial_message: str | None,
        messages: Messages
    ) -> Agent:
        tool_context = ToolContext(
            definition.tool_keys(),
            agent_id
        )
        spawner = self.create_spawner(agent_id)
        tools = self._tool_library_factory.create(
            tool_context, spawner, AgentTypes(self._agent_library.list_agent_types())
        )
        tools_documentation = generate_tools_documentation(tools.tools, tools.tool_syntax)
        system_prompt = definition.prompt().render(tools_documentation, self._project_tree)
        messages.seed_system_prompt(system_prompt)

        return Agent(
            agent_id,
            definition.agent_name(),
            tools,
            self._llm_provider,
            definition.model(),
            self.create_input(initial_message),
            self._event_bus,
            messages
        )
