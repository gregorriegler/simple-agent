from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Protocol

ChatMessage = dict[str, Any]
ChatMessages = list[ChatMessage]


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    input_token_limit: int | None = None


@dataclass
class LLMResponse:
    content: str
    model: str = ""
    usage: TokenUsage | None = None
    provider_metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = TokenUsage()


class LLM(Protocol):
    @property
    def model(self) -> str: ...

    async def call_async(self, messages: ChatMessages) -> LLMResponse: ...


class LLMProvider(Protocol):
    def get(self, model_name: str | None = None) -> LLM: ...

    def get_available_models(self) -> list[str]: ...


class Messages:
    def __init__(
        self,
        messages: ChatMessages | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._messages: ChatMessages = list(messages) if messages is not None else []
        self.seed_system_prompt(system_prompt)

    def user_says(self, content: str, metadata: dict[str, Any] | None = None):
        self.add("user", content, metadata)

    def assistant_says(self, content: str, metadata: dict[str, Any] | None = None):
        self.add("assistant", content, metadata)

    def add(self, role: str, content: str, metadata: dict[str, Any] | None = None):
        if content:
            message: ChatMessage = {"role": role, "content": content}
            if metadata:
                message["metadata"] = metadata
            self._messages.append(message)

    def seed_system_prompt(self, content: str | None):
        if not content:
            return

        system_message = {"role": "system", "content": content}

        if self._messages and self._messages[0].get("role") == "system":
            self._messages[0] = system_message
            return

        self._messages.insert(0, system_message)

    def to_list(self) -> ChatMessages:
        return list(self._messages)

    def clear(self):
        system_prompt = None
        if self._messages and self._messages[0].get("role") == "system":
            system_prompt = self._messages[0].get("content")
        self._messages = []
        if system_prompt:
            self.seed_system_prompt(system_prompt)

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self) -> Iterator[ChatMessage]:
        return iter(self._messages)

    def __str__(self) -> str:
        return str(self._messages)
