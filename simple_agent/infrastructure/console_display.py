from simple_agent.application.display import Display
from simple_agent.application.io import IO
from simple_agent.infrastructure.stdio import StdIO


def _indent_lines(text, prefix="    "):
    lines = str(text).split('\n')
    return '\n'.join(f"{prefix}{line}" if line.strip() else line for line in lines)


class ConsoleDisplay(Display):

    def __init__(self, indent_level, agent_name, io):
        self.indent_level = indent_level
        self.io = io
        self.base_indent = "       " * (indent_level + 1)
        self.agent_prefix = "       " * indent_level + f"{agent_name}: "

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines:
            self.io.print(f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.io.print(f"{self.base_indent}{line}")

    def tool_result(self, result):
        lines = str(result).split('\n')
        first_three_lines = '\n'.join(lines[:3])
        if len(lines) > 3:
            first_three_lines += '\n... (truncated)'
        result = _indent_lines(first_three_lines, self.base_indent)
        self.io.print(f"\n{result}")

    def continue_session(self):
        self.io.print("Continuing session")

    def start_new_session(self):
        self.io.print("Starting new session")

    def exit(self):
        exit_msg = "       " * self.indent_level + "Exiting..."
        self.io.print(f"\n{exit_msg}")
