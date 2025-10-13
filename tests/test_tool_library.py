from simple_agent.agent_factories import create_default_agent_factory
from simple_agent.application.agent_factory_registry import AgentFactoryRegistry
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.input import Input
from simple_agent.tools import AllTools
from simple_agent.infrastructure.console.console_subagent_display import ConsoleSubagentDisplay
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.stdio import StdIO


class ToolLibraryStub(AllTools):
    def __init__(self, llm, io=None, interrupts=None, event_bus=None, display_event_handler=None):
        actual_io = io if io else StdIO()

        def create_subagent_display(agent_id, indent):
            subagent_display = ConsoleSubagentDisplay(indent, agent_id, actual_io, display_event_handler)
            if display_event_handler:
                display_event_handler.register_display(agent_id, subagent_display)
            return subagent_display

        create_subagent_input = lambda indent: Input(ConsoleUserInput(indent, actual_io))

        actual_event_bus = event_bus if event_bus is not None else SimpleEventBus()
        agent_factory_registry = AgentFactoryRegistry()
        agent_factory_registry.register(
            'default',
            create_default_agent_factory(
                llm,
                actual_event_bus,
                create_subagent_display,
                create_subagent_input,
                agent_factory_registry
            )
        )

        super().__init__(
            llm,
            event_bus=actual_event_bus,
            create_subagent_display=create_subagent_display,
            create_subagent_input=create_subagent_input,
            agent_factory_registry=agent_factory_registry
        )
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
