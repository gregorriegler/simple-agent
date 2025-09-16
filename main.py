#!/usr/bin/env -S uv run --script

import argparse
import sys

from claude.claude_client import chat
from message_exceptions import ChatError, ChatInterruptError
from agent import Agent
from system_prompt_generator import SystemPromptGenerator
from chat import Messages, load_messages
from console_display import ConsoleDisplay
from tools import ToolLibrary


def get_system_prompt():
    generator = SystemPromptGenerator()
    return generator.generate_system_prompt()


def main():
    parser = argparse.ArgumentParser(description="Claude API CLI with session support")
    parser.add_argument("-c", "--continue", action="store_true", help="Continue previous session")
    parser.add_argument("message", nargs="*", help="Message to send to Claude")

    args = parser.parse_args()
    start_message = None
    if len(sys.argv) > 1:
        start_message = " ".join(sys.argv[1:])
    if args.message:
        start_message = " ".join(args.message)
    continue_session = getattr(args, 'continue')

    system_prompt = get_system_prompt()

    messages = load_messages() if continue_session else Messages()
    print("Continuing session" if continue_session else "Starting new session")

    if start_message:
        messages.user_says(start_message)

    display = ConsoleDisplay()
    tools = ToolLibrary(chat)
    agent = Agent(system_prompt, chat, display, tools)

    try:
        agent.start(messages)
    except ChatInterruptError:
        display.exit()
        return 1
    except ChatError as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
