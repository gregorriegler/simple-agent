import json
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict
from infrastructure.claude.claude_config import claude_config

@dataclass()
class Messages:
    _messages: List[Dict[str, str]] = field(default_factory=list)

    def user_says(self, content: str):
        self.add("user", content)

    def assistant_says(self, content: str):
        self.add("assistant", content)

    def add(self, role: str, content: str):
        self._messages.append({"role": role, "content": content})

    def to_list(self) -> List[Dict[str, str]]:
        return list(self._messages)

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self):
        return iter(self._messages)

    def __str__(self) -> str:
        return str(self._messages)


def load_messages() -> 'Messages':
    session_file = claude_config.session_file_path
    if not os.path.exists(session_file):
        return Messages()

    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
            return Messages(chat_data if isinstance(chat_data, list) else [])
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Could not load session file {session_file}: {e}", file=sys.stderr)
        return Messages()


def save_messages(messages):
    session_file = claude_config.session_file_path
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(messages.to_list(), f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save session file {session_file}: {e}", file=sys.stderr)
