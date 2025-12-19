from dataclasses import dataclass
from typing import Protocol, List, Dict, Any


@dataclass
class RawToolCall:
    name: str
    arguments: str
    body: str = ""

    def header(self) -> str:
        if self.arguments:
            return f"🛠️ {self.name} {self.arguments}"
        return f"🛠️ {self.name}"

    def __str__(self) -> str:
        if self.arguments:
            if self.body:
                return f"🛠️ {self.name} {self.arguments} {self.body}"
            return f"🛠️ {self.name} {self.arguments}"
        return f"🛠️ {self.name}"


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

    def header(self):
        return self.raw_call.header()

    def __str__(self):
        return self.raw_call.__str__()


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

    def __init__(self, header: List[ToolArgument] = None, body: ToolArgument | None = None):
        self._header: List[ToolArgument] = header or []
        self._body: ToolArgument | None = body

    def __iter__(self):
        return iter(self._header)

    def __len__(self):
        return len(self._header)

    def __getitem__(self, key):
        if isinstance(key, str):
            # Support dict-like access by name
            for arg in self._header:
                if arg.name == key:
                    return arg
            raise KeyError(f"Argument '{key}' not found")
        return self._header[key]

    def __bool__(self):
        return bool(self._header) or self._body is not None

    @property
    def header(self) -> List[ToolArgument]:
        return self._header

    @property
    def body(self) -> ToolArgument | None:
        return self._body

    @property
    def all(self) -> List[ToolArgument]:
        """Return all arguments: header args followed by body (if present)."""
        if self._body:
            return self._header + [self._body]
        return self._header


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
    def examples(self) -> List[Dict[str, Any]]:
        ...

    async def execute(self, raw_call: RawToolCall) -> ToolResult:
        ...

    def get_template_variables(self) -> Dict[str, str]:
        ...


class ToolLibrary(Protocol):
    tools: List[Tool]

    def parse_message_and_tools(self, text: str) -> MessageAndParsedTools:
        ...

    async def execute_parsed_tool(self, parsed_tool: ParsedTool) -> ToolResult:
        ...
