#!/usr/bin/env python

import argparse
import json
import os

from claude_client import message_claude
from helpers import *
from tools import ToolLibrary


def load_session(session_file):
    """Load conversation history from session file."""
    if not os.path.exists(session_file):
        return []
    
    try:
        with open(session_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Could not load session file {session_file}: {e}", file=sys.stderr)
        return []

def save_session(messages):
    session_file = "claude-session.json"
    try:
        with open(session_file, 'w') as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save session file {session_file}: {e}", file=sys.stderr)

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

    start_chat(start_message, new, message_claude, save_session=save_session)


def start_chat(start_message, new, message_claude, rounds=999999, save_session=save_session):
    system_prompt = get_system_prompt()
    tools = ToolLibrary()

    if new:
        messages = []
        print(f"Starting new session")
    else:
        messages = load_session("claude-session.json")
        print(f"Continuing session")
    
    messages.append({
        "role": "user",
        "content": start_message
    })

    for _ in range(rounds):
        answer = message_claude(messages, system_prompt)
        print(f"\nClaude: {answer}")
        messages.append({
            "role": "assistant",
            "content": answer
        })

        try:
            user_input = input("\nPress Enter to continue or type a message to add: ")
            if user_input.strip():
                messages.append({
                    "role": "user",
                    "content": user_input
                })
                continue
        except EOFError:
            print("\nExiting...")
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            break

        _, tool_result = tools.parse_and_execute(answer)

        if tool_result:
            messages.append({
                "role": "user",
                "content": f"[TOOL_RESULTS]\n{tool_result}\n"
            })

        save_session(messages)


if __name__ == "__main__":
    main()