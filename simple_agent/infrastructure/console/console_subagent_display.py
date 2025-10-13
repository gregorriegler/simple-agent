from simple_agent.application.io import IO
from simple_agent.infrastructure.console.console_display import ConsoleDisplay


class ConsoleSubagentDisplay(ConsoleDisplay):
    def __init__(self, indent_level, agent_id, io, display_event_handler):
        super().__init__(indent_level, "Subagent", io)
        self.agent_id = agent_id
        self.display_event_handler = display_event_handler

    def exit(self):
        if self.display_event_handler:
            del self.display_event_handler.displays[self.agent_id]
