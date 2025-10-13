from simple_agent.application.io import IO
from simple_agent.infrastructure.console_display import ConsoleDisplay


class ConsoleSubagentDisplay(ConsoleDisplay):
    def __init__(self, indent_level=1, io: IO | None = None):
        super().__init__(indent_level, "Subagent", io)

    def exit(self):
        pass
