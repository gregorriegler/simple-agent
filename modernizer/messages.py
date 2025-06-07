from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass(frozen=True)
class Messages:
    _messages: List[Dict[str, str]] = field(default_factory=list)

    def add(self, role: str, content: str) -> 'Messages':
        new_messages = list(self._messages)
        new_messages.append({"role": role, "content": content})
        return Messages(new_messages)
    
    def to_list(self) -> List[Dict[str, str]]:
        return list(self._messages)
    
    def __len__(self) -> int:
        return len(self._messages)
    
    def __iter__(self):
        return iter(self._messages)
    
    def __str__(self) -> str:
        return str(self._messages)
