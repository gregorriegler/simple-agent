from simple_agent.application.display import Display
from simple_agent.application.io import IO
from simple_agent.application.tool_library import ToolResult
from simple_agent.infrastructure.stdio import StdIO


def _indent_lines(text, prefix="    "):
    lines = str(text).split("\n")
    return "\n".join(f"{prefix}{line}" if line.strip() else line for line in lines)


class ConsoleDisplay(Display):

    def __init__(self, indent_level, agent_name, io):
        self.indent_level = indent_level
        self.io = io
        self.base_indent = "       " * (indent_level + 1)
        self.agent_prefix = "       " * indent_level + f"{agent_name}: "

    def assistant_says(self, message):
        lines = str(message).split("\n")
        if lines:
            self.io.print(f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.io.print(f"{self.base_indent}{line}")

    def user_says(self, message):
        pass

    def tool_call(self, call_id, tool):
        pass

    def tool_result(self, call_id, result: ToolResult):
        message = result.message if result else ""
        lines = message.split("\n") if message else [""]
        if result.success:
            display_lines = lines[:3]
            if len(lines) > 3:
                display_lines = display_lines + ['... (truncated)']
        else:
            display_lines = lines
        display_text = "\n".join(display_lines)
        formatted = _indent_lines(display_text, self.base_indent)
        self.io.print(f"\n{formatted}")

    def continue_session(self):
        self.io.print("Continuing session")

    def start_new_session(self):
        self.io.print("Starting new session")

    def waiting_for_input(self):
        pass

    def interrupted(self):
        interrupted_msg = "       " * self.indent_level + "[Session interrupted by user]"
        self.io.print(f"\n{interrupted_msg}")

    def exit(self):
        exit_msg = "       " * self.indent_level + "Exiting..."
        self.io.print(f"\n{exit_msg}")
