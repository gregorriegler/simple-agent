import json
import shlex
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from .tool_results import ToolResult


def is_true(value: Any) -> bool:
    """A flag is true as a JSON boolean or under its text spellings."""
    return value is True or str(value).lower() in ("true", "1")


@dataclass
class ToolCall:
    """
    A tool call as the model made it: its name and named arguments, typed
    per the tool's declaration, with the provider's ids.
    """

    name: str
    named_arguments: dict[str, Any] = field(default_factory=dict)
    provider_state: dict[str, Any] = field(default_factory=dict)


class ToolDeclaration(Protocol):
    """What a call needs to know about its tool: its name and declared arguments."""

    name: str
    arguments: "ToolArguments"


ToolDeclarations = Mapping[str, ToolDeclaration]


class ToolInvocation:
    """A bound call paired with the tool that runs it."""

    def __init__(self, call: ToolCall, tool: "Tool"):
        self.call = call
        self.tool = tool

    @property
    def name(self) -> str:
        return self.call.name

    async def execute(self) -> ToolResult:
        return await self.tool.execute(self.call)


@dataclass
class AssistantTurn:
    message: str
    invocations: list[ToolInvocation]

    def __iter__(self):
        yield self.message
        yield self.invocations


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


def _as_number(value: Any, kind: type) -> Any:
    try:
        return kind(value)
    except (TypeError, ValueError):
        return str(value)


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

    def coerce(self, value: Any) -> Any:
        """
        The value as the declared type: a flag from its spellings, a number
        from its text, else text. A value that is no number stays text.
        """
        if self.is_flag:
            return is_true(value)
        if self.json_type == "integer":
            return _as_number(value, int)
        if self.json_type == "number":
            return _as_number(value, float)
        return str(value)


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

    def coerce(self, named: dict[str, Any]) -> dict[str, Any]:
        """Every present value as its declared type; undeclared values as they are."""
        declared = {arg.name: arg for arg in self.all}
        return {
            name: declared[name].coerce(value) if name in declared else value
            for name, value in named.items()
        }

    def render_header(self, named: dict[str, Any]) -> str:
        """
        The positional header text for named values, the inverse of binding:
        a value is shell-quoted when needed, and a true flag appears by name.
        The last positional argument absorbs any leftover tokens when it is
        bound, so it is written as it is unless it carries quotes itself.
        """
        if self.single_positional:
            return str(named.get(self.single_positional.name, ""))
        positional = self.positional
        parts = [
            self._quoted(str(named[arg.name]), last=arg is positional[-1])
            for arg in positional
            if arg.name in named
        ]
        parts.extend(flag.name for flag in self.flags if named.get(flag.name))
        return " ".join(parts)

    @staticmethod
    def _quoted(value: str, last: bool) -> str:
        quoted = any(quote in value for quote in "'\"")
        spaced = not value or any(char.isspace() for char in value)
        if quoted or (spaced and not last):
            return shlex.quote(value)
        return value


def describe_call(call: ToolCall) -> str:
    """The call on one line: its name, then each named argument as JSON."""
    arguments = (
        f"{name}={json.dumps(value)}" for name, value in call.named_arguments.items()
    )
    return " ".join((call.name, *arguments))


def call_header(call: ToolCall, declarations: ToolDeclarations) -> str:
    """
    The call as one line of command text: its name and positional header.
    A call to a tool not declared renders its values in order.
    """
    tool = declarations.get(call.name)
    if tool is None:
        text = " ".join(str(value) for value in call.named_arguments.values())
    else:
        text = tool.arguments.render_header(call.named_arguments)
    return " ".join(part for part in (call.name, text) if part)


class Tool(Protocol):
    name: str
    description: str
    arguments: ToolArguments
    examples: list[dict[str, Any]]

    async def execute(self, call: ToolCall) -> ToolResult: ...

    def get_template_variables(self) -> dict[str, str]: ...


class ToolLibrary(Protocol):
    tools: list[Tool]

    def resolve_tool_calls(
        self, tool_calls: list[ToolCall], message: str
    ) -> AssistantTurn: ...

    async def execute_tool_call(self, invocation: ToolInvocation) -> ToolResult: ...
