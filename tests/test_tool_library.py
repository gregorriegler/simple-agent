from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.app_context import AppContext
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.input import Input
from simple_agent.tools import AllTools
from simple_agent.application.subagent_context import SubagentContext
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.infrastructure.all_tools_factory import AllToolsFactory
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from simple_agent.application.tool_library_factory import ToolLibraryFactory


class ToolLibraryStub(AllTools):
    def __init__(
        self,
        llm,
        io=None,
        interrupts=None,
        event_bus=None,
        subagent_context: SubagentContext | None = None,
        tool_keys: list[str] | None = None
    ):
        actual_io = io if io else StdIO()

        create_subagent_input = lambda indent: Input(ConsoleUserInput(indent, actual_io))

        from simple_agent.application.session_storage import NoOpSessionStorage
        actual_event_bus = event_bus if event_bus is not None else SimpleEventBus()
        actual_subagent_context = subagent_context
        if actual_subagent_context is None:
            tool_library_factory = AllToolsFactory()
            agent_library = BuiltinAgentLibrary()
            app_context = AppContext(
                llm=llm,
                event_bus=actual_event_bus,
                session_storage=NoOpSessionStorage(),
                tool_library_factory=tool_library_factory,
                agent_library=agent_library,
                create_subagent_input=create_subagent_input,
            )
            create_agent = AgentFactory(app_context)

            actual_subagent_context = SubagentContext(
                create_agent,
                create_subagent_input,
                1,
                "Agent",
                actual_event_bus
            )

        super().__init__(tool_keys=tool_keys, subagent_context=actual_subagent_context)
        self.interrupts = interrupts or []
        self.counter = 0

    def execute_parsed_tool(self, parsed_tool):
        if self.interrupts and self.counter < len(self.interrupts) and self.interrupts[self.counter]:
            self.counter += 1
            raise KeyboardInterrupt()
        args = parsed_tool.arguments if parsed_tool.arguments else None
        result = parsed_tool.tool_instance.execute(args)
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
        tool_keys: list[str],
        subagent_context: SubagentContext
    ) -> AllTools:
        return ToolLibraryStub(
            self._llm,
            io=self._io,
            interrupts=self._interrupts,
            event_bus=self._event_bus,
            subagent_context=subagent_context,
            tool_keys=tool_keys
        )
