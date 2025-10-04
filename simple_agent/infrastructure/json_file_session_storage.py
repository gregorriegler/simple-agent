import json
import os
import sys

from simple_agent.application.llm import Messages
from simple_agent.application.session_storage import SessionStorage
from .claude.claude_config import claude_config


class JsonFileSessionStorage(SessionStorage):

    def __init__(self, path=None):
        self.path = path or claude_config.session_file_path

    def load(self) -> Messages:
        if not os.path.exists(self.path):
            return Messages()
        try:
            with open(self.path, "r", encoding="utf-8") as session_file:
                raw_data = json.load(session_file)
        except json.JSONDecodeError as error:
            print(f"Warning: Could not load session file {self.path}: {error}", file=sys.stderr)
            return Messages()
        except Exception as error:
            print(f"Warning: Could not load session file {self.path}: {error}", file=sys.stderr)
            return Messages()
        if isinstance(raw_data, list):
            return Messages(raw_data)
        return Messages()

    def save(self, messages: Messages) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as session_file:
                json.dump(messages.to_list(), session_file, indent=2)
        except Exception as error:
            print(f"Warning: Could not save session file {self.path}: {error}", file=sys.stderr)
