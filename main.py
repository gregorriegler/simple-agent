#!/usr/bin/env -S uv run --script

import argparse
from dataclasses import dataclass

from application.agent import Agent
from application.chat import Messages
from application.session_storage import SessionStorage
from infrastructure.claude.claude_client import ClaudeChat
from infrastructure.console_display import ConsoleDisplay
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
    claude_chat = ClaudeChat()
    session_storage = JsonFileSessionStorage()
    run_session(args, display, session_storage, claude_chat, 999999)


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


def run_session(args: SessionArgs, display, session_storage: SessionStorage, chat, rounds):
    messages = session_storage.load() if args.continue_session else Messages()
    if args.start_message:
        messages.user_says(args.start_message)
    if args.continue_session:
        display.continue_session()
    else:
        display.start_new_session()
    tool_library = ToolLibrary(chat)
    system_prompt = SystemPromptGenerator().generate_system_prompt()
    agent = Agent(chat, system_prompt, tool_library, display, session_storage)
    agent.start(messages, rounds)


if __name__ == "__main__":
    main()

