#!/usr/bin/env -S uv run --script

import argparse

from simple_agent.application.input import Input
from simple_agent.application.session import run_session, SessionArgs
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.console_display import ConsoleDisplay
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage
from simple_agent.system_prompt_generator import SystemPromptGenerator


def main():
    args = parse_args()
    display = ConsoleDisplay()
    user_input = Input(display)
    if args.start_message:
        user_input.stack(args.start_message)
    session_storage = JsonFileSessionStorage()
    claude_chat = ClaudeLLM()
    system_prompt = lambda : SystemPromptGenerator().generate_system_prompt()
    run_session(args.continue_session, user_input, display, session_storage, claude_chat, system_prompt)


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


if __name__ == "__main__":
    main()
