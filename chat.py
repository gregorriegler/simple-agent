import json
import os
import sys

from application.chat import Messages
from infrastructure.claude.claude_config import claude_config


def load_messages() -> Messages:
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


def save_messages(messages: Messages):
    session_file = claude_config.session_file_path
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(messages.to_list(), f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save session file {session_file}: {e}", file=sys.stderr)
