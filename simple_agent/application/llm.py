from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from .model_info import ModelInfo
from .tool_library import RawToolCall, UnboundToolCall

T = TypeVar("T", covariant=True)


class MessageRenderer(Protocol[T]):
    """
    One method per kind of message. A message hands itself to the method
    that knows it, so an adapter maps every message to its own wire format
    without asking what it is.
    """

    def system(self, message: "SystemMessage") -> T: ...

    def user(self, message: "UserMessage") -> T: ...

    def assistant(self, message: "AssistantMessage") -> T: ...

    def tool_result(self, message: "ToolResultMessage") -> T: ...


@dataclass
class SystemMessage:
    content: str

    def render(self, renderer: MessageRenderer[T]) -> T:
        return renderer.system(self)


@dataclass
class UserMessage:
    content: str

    def render(self, renderer: MessageRenderer[T]) -> T:
        return renderer.user(self)


@dataclass
class AssistantMessage:
    """What the model said: its text and the tool calls it made, if any."""

    content: str
    tool_calls: list[RawToolCall] = field(default_factory=list)

    def render(self, renderer: MessageRenderer[T]) -> T:
        return renderer.assistant(self)


@dataclass
class ToolResultMessage:
    """The output of one tool call, paired with the call it answers."""

    call: RawToolCall
    content: str

    def render(self, renderer: MessageRenderer[T]) -> T:
        return renderer.tool_result(self)


ChatMessage = SystemMessage | UserMessage | AssistantMessage | ToolResultMessage
ChatMessages = list[ChatMessage]


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    answer: str
    tool_calls: list[UnboundToolCall] = field(default_factory=list)
    message: str | None = None
    model: str = ""
    usage: TokenUsage | None = None
    thought: str = ""

    def __post_init__(self):
        if self.usage is None:
            self.usage = TokenUsage()
        if self.message is None:
            self.message = self.answer

    def token_usage_display(self) -> str:
        input_tokens = self.usage.input_tokens if self.usage else 0
        max_tokens = ModelInfo.get_context_window(self.model)
        if max_tokens == 0:
            return "0.0%"
        percentage = (input_tokens / max_tokens) * 100
        return f"{percentage:.1f}%"


class LLM(Protocol):
    @property
    def model(self) -> str: ...

    async def call_async(self, messages: ChatMessages) -> LLMResponse: ...


class LLMProvider(Protocol):
    def get(self, model_name: str | None = None, tools: list | None = None) -> LLM: ...

    def get_available_models(self) -> list[str]: ...

    def tool_syntax(self, model_name: str | None = None) -> str: ...


class Messages:
    def __init__(
        self,
        messages: ChatMessages | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._messages: ChatMessages = list(messages) if messages is not None else []
        self.seed_system_prompt(system_prompt)

    def user_says(self, content: str):
        if content:
            self._messages.append(UserMessage(content))

    def assistant_says(
        self, content: str, tool_calls: list[RawToolCall] | None = None
    ) -> None:
        if content or tool_calls:
            self._messages.append(AssistantMessage(content, tool_calls or []))

    def tool_result(self, call: RawToolCall, output: str) -> None:
        self._messages.append(ToolResultMessage(call, output))

    def seed_system_prompt(self, content: str | None):
        if not content:
            return

        system_message = SystemMessage(content)

        if self._system_prompt() is not None:
            self._messages[0] = system_message
            return

        self._messages.insert(0, system_message)

    def to_list(self) -> ChatMessages:
        return list(self._messages)

    def clear(self):
        system_prompt = self._system_prompt()
        self._messages = []
        self.seed_system_prompt(system_prompt)

    def _system_prompt(self) -> str | None:
        first = self._messages[0] if self._messages else None
        if isinstance(first, SystemMessage):
            return first.content
        return None

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self) -> Iterator[ChatMessage]:
        return iter(self._messages)

    def __str__(self) -> str:
        return str(self._messages)
