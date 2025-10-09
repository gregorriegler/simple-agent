from simple_agent.application.user_input import UserInput
from simple_agent.application.io import IO
from simple_agent.infrastructure.stdio import StdIO


class ConsoleUserInput(UserInput):

    def __init__(self, indent_level=0, io: IO | None = None, allow_escape: bool = True):
        self.indent_level = indent_level
        self.io = io or StdIO()
        self.allow_escape = allow_escape

    def read(self) -> str:
        prompt = "\n" + "       " * self.indent_level + "Press Enter to continue or type a message to add: "
        return self.io.input(prompt).strip()

    def escape_requested(self) -> bool:
        if not self.allow_escape:
            return False
        return self.io.escape_requested()
