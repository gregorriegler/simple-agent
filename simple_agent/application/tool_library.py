from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from .tool_results import ToolResult

if TYPE_CHECKING:
    from .tool_syntax import ToolSyntax


@dataclass
class RawToolCall:
    name: str
    arguments: str
    body: str = ""
    thought_signature: str = ""
    named_arguments: dict[str, Any] = field(default_factory=dict)
    native_id: str = ""

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


class ToolCall:
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
        return self.raw_call.__str__()


@dataclass
class AssistantTurn:
    message: str
    tool_calls: list[ToolCall]

    def __iter__(self):
        yield self.message
        yield self.tool_calls


_JSON_TYPES = {
    "string": "string",
    "str": "string",
    "integer": "integer",
    "int": "integer",
    "number": "number",
    "float": "number",
    "boolean": "boolean",
    "bool": "boolean",
}


@dataclass
class ToolArgument:
    name: str
    description: str
    required: bool = True
    type: str = "string"

    @property
    def json_type(self) -> str:
        """The JSON schema type native adapters declare; unknown types are text."""
        return _JSON_TYPES.get(self.type, "string")

    @property
    def is_flag(self) -> bool:
        return self.json_type == "boolean"


class ToolArguments:
    def __init__(
        self, header: list[ToolArgument] | None = None, body: ToolArgument | None = None
    ):
        self._header: list[ToolArgument] = header or []
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
    def header(self) -> list[ToolArgument]:
        return self._header

    @property
    def body(self) -> ToolArgument | None:
        return self._body

    @property
    def flags(self) -> list[ToolArgument]:
        return [arg for arg in self._header if arg.is_flag]

    @property
    def positional(self) -> list[ToolArgument]:
        return [arg for arg in self._header if not arg.is_flag]

    @property
    def single_positional(self) -> ToolArgument | None:
        """The one header argument that takes the header text as written."""
        if self.flags or len(self.positional) != 1:
            return None
        return self.positional[0]

    @property
    def all(self) -> list[ToolArgument]:
        """Return all arguments: header args followed by body (if present)."""
        if self._body:
            return self._header + [self._body]
        return self._header


class Tool(Protocol):
    name: str
    description: str
    arguments: ToolArguments
    examples: list[dict[str, Any]]

    async def execute(self, raw_call: RawToolCall) -> ToolResult: ...

    def get_template_variables(self) -> dict[str, str]: ...


class ToolLibrary(Protocol):
    tools: list[Tool]
    tool_syntax: "ToolSyntax"

    def parse_and_resolve(self, text: str) -> AssistantTurn: ...

    def resolve_tool_calls(
        self, tool_calls: list[RawToolCall], message: str
    ) -> AssistantTurn: ...

    async def execute_tool_call(self, tool_call: ToolCall) -> ToolResult: ...
