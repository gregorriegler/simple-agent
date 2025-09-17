#!/usr/bin/env -S uv run --script

import argparse

from claude.claude_client import message_claude
from agent import Agent
from system_prompt_generator import SystemPromptGenerator
from chat import Messages, load_chat
from console_display import ConsoleDisplay
from tools import ToolLibrary


def main():
    parser = argparse.ArgumentParser(description="Claude API CLI with session support")
    parser.add_argument("-c", "--continue", action="store_true", help="Continue previous session")
    parser.add_argument("message", nargs="*", help="Message to send to Claude")
    args = parser.parse_args()

    continue_session = get_continue_session(args)
    start_message = get_start_message(args)
    messages = get_starting_messages(continue_session, start_message)

    system_prompt = SystemPromptGenerator().generate_system_prompt()

    print("Continuing session" if continue_session else "Starting new session")

    display = ConsoleDisplay()
    tool_library = ToolLibrary(message_claude)
    agent = Agent(system_prompt, message_claude, display, tool_library)
    agent.start(messages)


def get_starting_messages(continue_session, start_message):
    messages = load_chat() if continue_session else Messages()
    if start_message:
        messages.user_says(start_message)
    return messages


def get_continue_session(args):
    return getattr(args, 'continue')


def get_start_message(args):
    start_message = None
    if args.message:
        start_message = " ".join(args.message)
    return start_message


if __name__ == "__main__":
    main()
