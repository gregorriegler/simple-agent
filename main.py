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
    start_message = None
    if args.message:
        start_message = " ".join(args.message)
    continue_session = getattr(args, 'continue')

    generator = SystemPromptGenerator()
    system_prompt = generator.generate_system_prompt()

    messages = load_chat() if continue_session else Messages()
    print("Continuing session" if continue_session else "Starting new session")

    if start_message:
        messages.user_says(start_message)

    Agent(system_prompt, message_claude, ConsoleDisplay(), ToolLibrary(message_claude)).start(messages)


if __name__ == "__main__":
    main()
