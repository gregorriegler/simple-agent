#!/usr/bin/env python

import argparse
import sys

from claude_client import message_claude
from agent import start_chat, save_chat
from system_prompt_generator import SystemPromptGenerator


def get_system_prompt():
    """Get the system prompt with dynamically populated tools"""
    generator = SystemPromptGenerator()
    return generator.get_system_prompt_for_llm()


def main():
    parser = argparse.ArgumentParser(description="Claude API CLI with session support")
    parser.add_argument("--new", action="store_true", help="Start a new session (clear history)")
    parser.add_argument("message", nargs="*", help="Message to send to Claude")

    args = parser.parse_args()
    start_message = None
    if len(sys.argv) > 1:
        start_message = " ".join(sys.argv[1:])
    if args.message:
        start_message = " ".join(args.message)
    new = args.new

    system_prompt = get_system_prompt()
    start_chat(system_prompt, start_message, new, message_claude, save_chat=save_chat)


if __name__ == "__main__":
    main()
