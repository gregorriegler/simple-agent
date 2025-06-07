from dataclasses import dataclass, field
from typing import List, Dict

@dataclass(frozen=True)
class Chat:
    _messages: List[Dict[str, str]] = field(default_factory=list)

    def userSays(self, content: str) -> 'Chat':
        return self.add("user", content)

    def add(self, role: str, content: str) -> 'Chat':
        new_messages = list(self._messages)
        new_messages.append({"role": role, "content": content})
        return Chat(new_messages)
    
    def to_list(self) -> List[Dict[str, str]]:
        return list(self._messages)
    
    def __len__(self) -> int:
        return len(self._messages)
    
    def __iter__(self):
        return iter(self._messages)
    
    def __str__(self) -> str:
        return str(self._messages)