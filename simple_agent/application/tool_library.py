from dataclasses import dataclass
from typing import Protocol, List, Dict, Any


@dataclass
class RawToolCall:
    name: str
    arguments: str
    body: str = ""


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
    def __init__(self, raw_call, tool_instance):
        self.raw_call = raw_call
        self.tool_instance = tool_instance

    @property
    def name(self):
        return self.raw_call.name

    @property
    def arguments(self):
        return self.raw_call.arguments

    @property
    def body(self):
        return self.raw_call.body

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


@dataclass
class ToolArgument:
    name: str
    description: str
    required: bool = True
    type: str = "string"


class ToolArguments:
    """Wrapper class for a collection of ToolArguments.

    Addresses primitive obsession by encapsulating behavior specific to
    collections of tool arguments.
    """

    def __init__(self, arguments: List[ToolArgument] = None):
        self._arguments: List[ToolArgument] = arguments or []

    def __iter__(self):
        return iter(self._arguments)

    def __len__(self):
        return len(self._arguments)

    def __getitem__(self, key):
        if isinstance(key, str):
            # Support dict-like access by name
            for arg in self._arguments:
                if arg.name == key:
                    return arg
            raise KeyError(f"Argument '{key}' not found")
        return self._arguments[key]

    def __bool__(self):
        return bool(self._arguments)

    def find_by_name(self, name: str) -> ToolArgument | None:
        """Find an argument by name, returning None if not found."""
        for arg in self._arguments:
            if arg.name == name:
                return arg
        return None

    @property
    def required(self) -> 'ToolArguments':
        """Return a new ToolArguments containing only required arguments."""
        return ToolArguments([arg for arg in self._arguments if arg.required])

    @property
    def optional(self) -> 'ToolArguments':
        """Return a new ToolArguments containing only optional arguments."""
        return ToolArguments([arg for arg in self._arguments if not arg.required])


class Tool(Protocol):

    @property
    def name(self) -> str:
        ...

    @property
    def description(self) -> str:
        ...

    @property
    def arguments(self) -> ToolArguments:
        ...

    @property
    def body(self) -> ToolArgument | None:
        ...

    @property
    def examples(self) -> List[Dict[str, Any]]:
        ...

    def execute(self, raw_call: RawToolCall) -> ToolResult:
        ...

    def get_template_variables(self) -> Dict[str, str]:
        ...


class ToolLibrary(Protocol):
    tools: List[Tool]

    def parse_message_and_tools(self, text: str) -> MessageAndParsedTools:
        ...

    def execute_parsed_tool(self, parsed_tool: ParsedTool) -> ToolResult:
        ...
