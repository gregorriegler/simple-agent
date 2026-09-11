import shlex
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Protocol

from .tool_results import ToolResult

if TYPE_CHECKING:
    from .tool_syntax import ToolSyntax


def is_true(value: Any) -> bool:
    """A flag is true as a JSON boolean or under its text spellings."""
    return value is True or str(value).lower() in ("true", "1")


@dataclass
class ToolCall:
    """
    A tool call as the model made it: its name and named arguments, with
    the provider's ids. Once bound to a tool it knows the tool's declared
    arguments and can render its positional header and body text from them.
    """

    name: str
    named_arguments: dict[str, Any] = field(default_factory=dict)
    thought_signature: str = ""
    native_id: str = ""
    declaration: "ToolArguments | None" = field(default=None, compare=False, repr=False)

    def bind(self, tool: "ToolDeclaration | None") -> "ToolCall":
        if tool is None:
            return self
        return replace(
            self,
            named_arguments=tool.arguments.coerce(self.named_arguments),
            declaration=tool.arguments,
        )

    def header(self) -> str:
        return " ".join(part for part in (self.name, self._arguments_text()) if part)

    def body(self) -> str:
        if self.declaration is None:
            return ""
        return self.declaration.render_body(self.named_arguments)

    def _arguments_text(self) -> str:
        if self.declaration is None:
            return " ".join(str(value) for value in self.named_arguments.values())
        return self.declaration.render_header(self.named_arguments)

    def __str__(self) -> str:
        return " ".join(part for part in (self.header(), self.body()) if part)


class ToolDeclaration(Protocol):
    """What a call needs to know about its tool: its name and declared arguments."""

    name: str
    arguments: "ToolArguments"


ToolDeclarations = Mapping[str, ToolDeclaration]


class UnboundToolCall(Protocol):
    """
    A call as an adapter delivered it, before the tool it names is known.
    Binding to no tool at all yields the best call there is without one.
    """

    name: str

    def bind(self, tool: ToolDeclaration | None) -> ToolCall: ...


def bind_call(call: UnboundToolCall, declarations: ToolDeclarations) -> ToolCall:
    return call.bind(declarations.get(call.name))


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
        """The value as the declared type: a flag from its spellings, else text."""
        if self.is_flag:
            return is_true(value)
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
        if last and not any(quote in value for quote in "'\""):
            return value
        return shlex.quote(value)

    def render_body(self, named: dict[str, Any]) -> str:
        if self._body is None:
            return ""
        return str(named.get(self._body.name, ""))


class Tool(Protocol):
    name: str
    description: str
    arguments: ToolArguments
    examples: list[dict[str, Any]]

    async def execute(self, call: ToolCall) -> ToolResult: ...

    def get_template_variables(self) -> dict[str, str]: ...


class ToolLibrary(Protocol):
    tools: list[Tool]
    tool_syntax: "ToolSyntax"

    def parse_and_resolve(self, text: str) -> AssistantTurn: ...

    def resolve_tool_calls(
        self, tool_calls: list[ToolCall], message: str
    ) -> AssistantTurn: ...

    async def execute_tool_call(self, invocation: ToolInvocation) -> ToolResult: ...
