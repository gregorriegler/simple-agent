from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

ChatMessage = dict[str, str]
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
    usage: TokenUsage = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = TokenUsage()


class LLM(Protocol):
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

    def user_says(self, content: str):
        self.add("user", content)

    def assistant_says(self, content: str):
        self.add("assistant", content)

    def add(self, role: str, content: str):
        if content:
            self._messages.append({"role": role, "content": content})

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
