#!/usr/bin/env python

import argparse
import sys

from claude_client import message_claude
from agent import Agent
from system_prompt_generator import SystemPromptGenerator
from chat import Chat, load_chat


def get_system_prompt():
    """Get the system prompt with dynamically populated tools"""
    generator = SystemPromptGenerator()
    return generator.get_system_prompt_for_llm()


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

    # Handle chat creation logic that was previously in start_chat
    chat = load_chat("claude-session.json") if continue_session else Chat()
    print("Continuing session" if continue_session else "Starting new session")

    if start_message:
        chat = chat.userSays(start_message)

    Agent(system_prompt, message_claude).start(chat)


if __name__ == "__main__":
    main()
