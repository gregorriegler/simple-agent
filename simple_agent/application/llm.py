from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol

from .model_info import ModelInfo
from .tool_library import RawToolCall


@dataclass
class AssistantMessage:
    """An assistant turn as the model made it: its text and its tool calls."""

    content: str
    tool_calls: list[RawToolCall]


@dataclass
class ToolResultMessage:
    """The output of one tool call, paired with the call it answers."""

    call: RawToolCall
    content: str


ChatMessage = dict[str, str] | AssistantMessage | ToolResultMessage
ChatMessages = list[ChatMessage]


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    answer: str
    tool_calls: list[RawToolCall] = field(default_factory=list)
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
        self.add("user", content)

    def assistant_says(self, content: str):
        self.add("assistant", content)

    def assistant_turn(self, content: str, tool_calls: list[RawToolCall]) -> None:
        self._messages.append(AssistantMessage(content, tool_calls))

    def tool_result(self, call: RawToolCall, output: str) -> None:
        self._messages.append(ToolResultMessage(call, output))

    def add(self, role: str, content: str):
        if content:
            self._messages.append({"role": role, "content": content})

    def seed_system_prompt(self, content: str | None):
        if not content:
            return

        system_message = {"role": "system", "content": content}

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
        if isinstance(first, dict) and first.get("role") == "system":
            return first.get("content", "")
        return None

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self) -> Iterator[ChatMessage]:
        return iter(self._messages)

    def __str__(self) -> str:
        return str(self._messages)
