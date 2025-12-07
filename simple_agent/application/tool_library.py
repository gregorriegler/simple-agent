from dataclasses import dataclass
from typing import Protocol, List, Dict, Any


@dataclass
class RawToolCall:
    name: str
    arguments: str


@dataclass
class ParsedMessage:
    message: str
    tool_calls: List[RawToolCall]


@dataclass
class ToolArgument:
    name: str
    description: str
    required: bool = True
    multiline: bool = False
    type: str = "string"


@dataclass
class ToolResult:
    message: str = ""
    success: bool = True
    display_title: str = ""
    display_body: str = ""
    display_language: str = ""

    def __str__(self) -> str:
        return self.message

    def do_continue(self) -> bool:
        raise NotImplementedError


@dataclass
class ContinueResult(ToolResult):
    def do_continue(self) -> bool:
        return True


@dataclass
class CompleteResult(ToolResult):
    def do_continue(self) -> bool:
        return False


class ParsedTool:
    def __init__(self, name, arguments, tool_instance):
        self.name = name
        self.arguments = arguments
        self.tool_instance = tool_instance

    def __str__(self):
        if self.arguments:
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

    @property
    def name(self) -> str:
        ...

    @property
    def description(self) -> str:
        ...

    @property
    def arguments(self) -> List[ToolArgument]:
        ...

    @property
    def examples(self) -> List[Dict[str, Any]]:
        ...

    def get_usage_info(self) -> str:
        ...

    def execute(self, *args, **kwargs) -> ToolResult:
        ...

    def finalize_documentation(self, doc: str, context: dict) -> str:
        ...


class ToolLibrary(Protocol):
    tools: List[Tool]

    def parse_message_and_tools(self, text: str) -> MessageAndParsedTools:
        ...

    def execute_parsed_tool(self, parsed_tool: ParsedTool) -> ToolResult:
        ...
