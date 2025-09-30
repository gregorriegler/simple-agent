from application.display import Display
import sys


class ConsoleDisplay(Display):

    def __init__(self, indent_level=0, agent_name="Agent", input_fn=input, print_fn=print):
        self.indent_level = indent_level
        self.print = print_fn
        self.base_indent = "       " * (indent_level + 1)  # 7 spaces per level
        self.agent_prefix = "       " * indent_level + f"{agent_name}: "
        self.input_fn = input_fn

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines:

            self.print(f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.print(f"{self.base_indent}{line}")

    def tool_result(self, result):
        lines = str(result).split('\n')
        first_three_lines = '\n'.join(lines[:3])
        if len(lines) > 3:
            first_three_lines += '\n... (truncated)'
        result = self._indent_lines(first_three_lines, self.base_indent)
        self.print(f"\n{result}")

    def continue_session(self):
        self.print("Continuing session")

    def start_new_session(self):
        self.print("Starting new session")

    def input(self) -> str:
        prompt = "       " * self.indent_level + "Press Enter to continue or type a message to add: "
        self.print(f"\n{prompt}", file=sys.stderr)
        return self.input_fn("").strip()

    def exit(self):
        exit_msg = "       " * self.indent_level + "Exiting..."
        self.print(f"\n{exit_msg}")

    def _indent_lines(self, text, prefix="    "):
        lines = str(text).split('\n')
        return '\n'.join(f"{prefix}{line}" if line.strip() else line for line in lines)
