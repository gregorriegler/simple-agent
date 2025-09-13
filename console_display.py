from agent import Display
import sys


class ConsoleDisplay(Display):

    def __init__(self, indent_level=0, print_fn=print, agent_type="Agent"):
        self.indent_level = indent_level
        self.print = print_fn
        self.agent_type = agent_type
        self.base_indent = "       " * (indent_level + 1)  # 7 spaces per level
        self.agent_prefix = "       " * indent_level + f"{agent_type}: "

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines:

            self.print(f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.print(f"{self.base_indent}{line}")

    def tool_about_to_execute(self, parsed_tool):
        indented_tool = self._indent_lines(str(parsed_tool), "       " * self.indent_level)
        self.print(f"\n{indented_tool}")

    def tool_result(self, result):
        result = self._indent_lines(result, self.base_indent)
        self.print(f"\n{result}")

    def input(self):
        prompt = "       " * self.indent_level + "Press Enter to continue or type a message to add: "
        self.print(f"\n{prompt}", file=sys.stderr)
        return input("")

    def exit(self):
        exit_msg = "       " * self.indent_level + "Exiting..."
        self.print(f"\n{exit_msg}")

    def _indent_lines(self, text, prefix="    "):
        lines = str(text).split('\n')
        return '\n'.join(f"{prefix}{line}" if line.strip() else line for line in lines)
