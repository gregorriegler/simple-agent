#!/usr/bin/env -S uv run --script

import argparse
from dataclasses import dataclass

from claude.claude_client import chat
from agent import Agent
from system_prompt_generator import SystemPromptGenerator
from chat import Messages, load_messages
from console_display import ConsoleDisplay
from tools import ToolLibrary


@dataclass
class SessionArgs:
    continue_session: bool
    start_message: str | None


def main():
    args = parse_args()
    display = ConsoleDisplay()
    run_session(args, display)


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


def run_session(args: SessionArgs, display):
    messages = load_messages() if args.continue_session else Messages()
    if args.start_message:
        messages.user_says(args.start_message)
    if args.continue_session:
        display.continue_session()
    else:
        display.start_new_session()
    tool_library = ToolLibrary(chat)
    system_prompt = SystemPromptGenerator().generate_system_prompt()
    agent = Agent(chat, system_prompt, tool_library, display)
    agent.start(messages)


if __name__ == "__main__":
    main()
