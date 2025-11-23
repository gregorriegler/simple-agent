from typing import Protocol, Iterator, Dict, List


ChatMessage = Dict[str, str]
ChatMessages = List[ChatMessage]


class LLM(Protocol):
    def __call__(self, messages: ChatMessages) -> str:
        ...


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

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self) -> Iterator[ChatMessage]:
        return iter(self._messages)

    def __str__(self) -> str:
        return str(self._messages)
