from dataclasses import dataclass, field
from typing import Protocol, Iterator, Dict, List


ChatMessage = Dict[str, str]
ChatMessages = List[ChatMessage]


class Chat(Protocol):

    def __call__(self, system_prompt: str, messages: ChatMessages) -> str:
        ...


@dataclass
class Messages:
    _messages: ChatMessages = field(default_factory=list)

    def user_says(self, content: str):
        self.add("user", content)

    def assistant_says(self, content: str):
        self.add("assistant", content)

    def add(self, role: str, content: str):
        if content:
            self._messages.append({"role": role, "content": content})

    def to_list(self) -> ChatMessages:
        return list(self._messages)

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self) -> Iterator[ChatMessage]:
        return iter(self._messages)

    def __str__(self) -> str:
        return str(self._messages)
