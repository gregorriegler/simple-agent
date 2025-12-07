from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.tool_library_factory import ToolContext
from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.tools import AllTools
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.tools.all_tools import AllToolsFactory
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from simple_agent.application.tool_library_factory import ToolLibraryFactory
from tests.user_input_stub import UserInputStub


class ToolLibraryStub(AllTools):
    def __init__(
        self,
        llm,
        io=None,
        interrupts=None,
        event_bus=None,
        tool_context: ToolContext | None = None,
        spawner=None,
        tool_keys: list[str] | None = None,
        agent_types: AgentTypes = None
    ):
        actual_io = io if io else StdIO()

        from simple_agent.application.session_storage import NoOpSessionStorage
        actual_event_bus = event_bus if event_bus is not None else SimpleEventBus()
        actual_tool_context = tool_context
        actual_spawner = spawner
        actual_agent_types = agent_types if agent_types is not None else AgentTypes.empty()
        if actual_tool_context is None:
            tool_library_factory = AllToolsFactory()
            agent_library = BuiltinAgentLibrary()
            session_storage = NoOpSessionStorage()
            agent_factory = AgentFactory(
                llm=llm,
                event_bus=actual_event_bus,
                session_storage=session_storage,
                tool_library_factory=tool_library_factory,
                agent_library=agent_library,
                user_input=UserInputStub(actual_io)
            )

            agent_id = AgentId("Agent")
            actual_tool_context = ToolContext(
                tool_keys or [],
                agent_id
            )
            actual_spawner = lambda agent_type, task_description: agent_factory.spawn_subagent(
                agent_id, agent_type, task_description, 1
            )
            actual_agent_types = AgentTypes(agent_library.list_agent_types())

        tool_syntax = EmojiBracketToolSyntax()
        super().__init__(tool_context=actual_tool_context, spawner=actual_spawner, agent_types=actual_agent_types, tool_syntax=tool_syntax)
        self.interrupts = interrupts or []
        self.counter = 0

    def execute_parsed_tool(self, parsed_tool):
        if self.interrupts and self.counter < len(self.interrupts) and self.interrupts[self.counter]:
            self.counter += 1
            raise KeyboardInterrupt()
        result = parsed_tool.tool_instance.execute(parsed_tool.raw_call)
        self.counter += 1
        return result


class ToolLibraryFactoryStub(ToolLibraryFactory):
    def __init__(
        self,
        llm,
        io=None,
        interrupts=None,
        event_bus=None,
        all_displays=None
    ):
        self._llm = llm
        self._io = io
        self._interrupts = interrupts
        self._event_bus = event_bus
        self._all_displays = all_displays

    def create(
        self,
        tool_context: ToolContext,
        spawner=None,
        agent_types: AgentTypes = AgentTypes.empty()
    ) -> AllTools:
        return ToolLibraryStub(
            self._llm,
            io=self._io,
            interrupts=self._interrupts,
            event_bus=self._event_bus,
            tool_context=tool_context,
            spawner=spawner
        )
