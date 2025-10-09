#!/usr/bin/env -S uv run --script

import argparse

from simple_agent.application.input import Input
from simple_agent.application.session import run_session, SessionArgs
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.claude.claude_config import load_claude_config
from simple_agent.infrastructure.console_display import ConsoleDisplay
from simple_agent.infrastructure.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage
from simple_agent.system_prompt_generator import generate_system_prompt


def main():
    args = parse_args()

    if args.show_system_prompt:
        from simple_agent.tools.tool_library import AllTools
        tool_library = AllTools()
        system_prompt = generate_system_prompt(tool_library)
        print(system_prompt)
        return

    display = ConsoleDisplay()
    user_input_port = ConsoleUserInput(display.indent_level, display.io)
    user_input = Input(user_input_port)
    if args.start_message:
        user_input.stack(args.start_message)
    session_storage = JsonFileSessionStorage()
    claude_config = load_claude_config()
    claude_chat = ClaudeLLM(claude_config)
    system_prompt_generator = lambda tool_library: generate_system_prompt(tool_library)
    run_session(args.continue_session, user_input, display, session_storage, claude_chat, system_prompt_generator)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Simple Agent")
    parser.add_argument("-c", "--continue", action="store_true", help="Continue previous session")
    parser.add_argument("-s", "--system-prompt", action="store_true", help="Print the current system prompt including AGENTS.md content")
    parser.add_argument("message", nargs="*", help="Message to send to Claude")
    parsed = parser.parse_args(argv)
    return SessionArgs(bool(getattr(parsed, "continue")), build_start_message(parsed.message), bool(getattr(parsed, "system_prompt")))


def build_start_message(message_parts):
    if not message_parts:
        return None
    return " ".join(message_parts)


if __name__ == "__main__":
    main()
