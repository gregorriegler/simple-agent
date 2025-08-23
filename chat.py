import json
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass(frozen=True)
class Chat:
    _messages: List[Dict[str, str]] = field(default_factory=list)

    def user_says(self, content: str) -> 'Chat':
        return self.add("user", content)

    def assistant_says(self, content: str) -> 'Chat':
        return self.add("assistant", content)

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


def load_chat(session_file: str = "claude-session.json") -> 'Chat':
    if not os.path.exists(session_file):
        return Chat()

    try:
        with open(session_file, 'r') as f:
            chat_data = json.load(f)
            return Chat(chat_data if isinstance(chat_data, list) else [])
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Could not load session file {session_file}: {e}", file=sys.stderr)
        return Chat()


def save_chat(chat):
    session_file = "claude-session.json"
    try:
        with open(session_file, 'w') as f:
            json.dump(chat.to_list(), f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save session file {session_file}: {e}", file=sys.stderr)
