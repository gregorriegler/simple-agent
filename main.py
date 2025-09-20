#!/usr/bin/env -S uv run --script

import argparse
from dataclasses import dataclass

from application.agent import Agent
from application.chat import Messages
from application.input import Input
from application.persisted_messages import PersistedMessages
from application.session_storage import SessionStorage
from infrastructure.claude.claude_client import ClaudeChat
from infrastructure.console_display import ConsoleDisplay
from infrastructure.console_escape_detector import ConsoleEscapeDetector
from infrastructure.json_file_session_storage import JsonFileSessionStorage
from system_prompt_generator import SystemPromptGenerator
from tools import ToolLibrary


@dataclass
class SessionArgs:
    continue_session: bool
    start_message: str | None


def main():
    args = parse_args()
    display = ConsoleDisplay()
    escape_detector = ConsoleEscapeDetector()
    user_input = Input(display, escape_detector)
    if args.start_message:
        user_input.stack(args.start_message)
    session_storage = JsonFileSessionStorage()
    claude_chat = ClaudeChat()
    run_session(args, user_input, display, session_storage, claude_chat)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Simple Agent")
    parser.add_argument("-c", "--continue", action="store_true", help="Continue previous session")
    parser.add_argument("message", nargs="*", help="Message to send to Claude")
    parsed = parser.parse_args(argv)
    return SessionArgs(bool(getattr(parsed, "continue")), build_start_message(parsed.message))


def build_start_message(message_parts):
    if not message_parts:
        return None
    return " ".join(message_parts)


def run_session(args: SessionArgs, user_input, display, session_storage: SessionStorage, chat, rounds=9999999):
    messages = session_storage.load() if args.continue_session else Messages()
    persisted_messages = PersistedMessages(messages, session_storage)

    if args.continue_session:
        display.continue_session()
    else:
        display.start_new_session()
    tool_library = ToolLibrary(chat)
    system_prompt = SystemPromptGenerator().generate_system_prompt()
    agent = Agent(chat, system_prompt, user_input, tool_library, display, session_storage)
    agent.start(persisted_messages, rounds)


if __name__ == "__main__":
    main()
