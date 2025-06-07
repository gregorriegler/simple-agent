#!/usr/bin/env python

import argparse
import os
import sys

from claude_client import message_claude
from helpers import *
from chat import Chat, load_chat, save_chat
from tools import ToolLibrary


def get_system_prompt():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    system_prompt_path = os.path.join(script_dir, "system-prompt.md")
    system_prompt = None
    if os.path.exists(system_prompt_path):
        system_prompt = read_file(system_prompt_path)
    return system_prompt


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

    start_chat(start_message, new, message_claude, save_chat=save_chat)


def start_chat(start_message, new, message_claude, rounds=999999, save_chat=save_chat):
    system_prompt = get_system_prompt()
    tools = ToolLibrary()

    chat = Chat() if new else load_chat("claude-session.json")
    print("Starting new session" if new else "Continuing session")
    
    if start_message:
        chat = chat.userSays(start_message)

    for _ in range(rounds):
        answer = message_claude(chat.to_list(), system_prompt)
        print(f"\nClaude: {answer}")
        chat = chat.assistantSays(answer)

        try:
            user_input = input("\nPress Enter to continue or type a message to add: ")
            if user_input.strip():
                chat = chat.userSays(user_input)
                continue
        except EOFError:
            print("\nExiting...")
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            break

        _, tool_result = tools.parse_and_execute(answer)

        if tool_result:
            chat = chat.userSays(tool_result)

        save_chat(chat)


if __name__ == "__main__":
    main()