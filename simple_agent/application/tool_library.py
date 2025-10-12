from dataclasses import dataclass
from typing import Protocol, List, Optional

@dataclass
class ToolResult:
    feedback: str

    def __init__(self, feedback=""):
        self.feedback = feedback

    def __str__(self) : return self.feedback

@dataclass
class ContinueResult(ToolResult):
    def __init__(self, feedback=""):
        super().__init__(feedback)


@dataclass
class CompleteResult(ToolResult):
    pass

class ParsedTool(Protocol):
    arguments: str | None
    tool_instance: object

@dataclass
class MessageAndParsedTools:
    message: str
    tools: List[ParsedTool]


class Tool(Protocol):

    def get_usage_info(self) -> str:
        ...

    def execute(self, *args, **kwargs) -> ToolResult:
        ...


class ToolLibrary(Protocol):
    tools: List[Tool]

    def parse_tool(self, text: str) -> MessageAndParsedTools:
        ...

    def execute_parsed_tool(self, parsed_tool: ParsedTool) -> ToolResult:
        ...
