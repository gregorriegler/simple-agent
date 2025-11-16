from simple_agent.application.io import IO
from simple_agent.infrastructure.console.console_display import ConsoleDisplay


class ConsoleSubagentDisplay(ConsoleDisplay):
    def __init__(self, indent_level, agent_id, agent_name, io):
        super().__init__(indent_level, agent_name or "Subagent", io)
        self.agent_id = agent_id
        self.agent_name = agent_name
