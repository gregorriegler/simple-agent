from dataclasses import dataclass
from typing import Protocol, List, Optional

@dataclass
class ToolResult:
    feedback: str

    def __init__(self, feedback=""):
        self.feedback = feedback

    def __str__(self) : return self.feedback

    def do_continue(self) -> bool:
        ...

@dataclass
class ContinueResult(ToolResult):
    def __init__(self, feedback=""):
        super().__init__(feedback)

    def do_continue(self) -> bool:
        return True


@dataclass
class CompleteResult(ToolResult):
    pass

    def do_continue(self) -> bool:
        return False

class ParsedTool:
    def __init__(self, name, arguments, tool_instance):
        self.name = name
        self.arguments = arguments
        self.tool_instance = tool_instance

    def __str__(self):
        if self.arguments:
            if '\n' in self.arguments:
                return f"🛠️ {self.name}\n{self.arguments}"
            else:
                return f"🛠️ {self.name} {self.arguments}"
        return f"🛠️ {self.name}"

@dataclass
class MessageAndParsedTools:
    message: str
    tools: List[ParsedTool]

    def __iter__(self):
        yield self.message
        yield self.tools


class Tool(Protocol):

    def get_usage_info(self) -> str:
        ...

    def execute(self, *args, **kwargs) -> ToolResult:
        ...


class ToolLibrary(Protocol):
    tools: List[Tool]

    def parse_message_and_tools(self, text: str) -> MessageAndParsedTools:
        ...

    def execute_parsed_tool(self, parsed_tool: ParsedTool) -> ToolResult:
        ...
