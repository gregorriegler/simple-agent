#!/usr/bin/env python

import requests
import json
import sys
import os
import argparse
from ToolFramework import ToolFramework
from helpers import *

api_key = read_file("claude-api-key.txt")
model = read_file("claude-model.txt")
system_prompt = None
if os.path.exists("system-prompt.txt"):
    system_prompt = read_file("system-prompt.txt")

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

def save_session(session_file, messages):
    """Save conversation history to session file."""
    try:
        with open(session_file, 'w') as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save session file {session_file}: {e}", file=sys.stderr)

def message_claude(messages):
    """Send a request to the Claude API with conversation history."""
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": model,
        "max_tokens": 4000,
        "messages": messages
    }
    
    # Add system prompt if provided
    if system_prompt:
        data["system"] = system_prompt
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude API CLI with session support")
    parser.add_argument("--new-session", action="store_true", help="Start a new session (clear history)")
    parser.add_argument("--session-file", default="claude-session.json", help="Session file name (default: claude-session.json)")
    parser.add_argument("message", nargs="*", help="Message to send to Claude")
    
    args = parser.parse_args()
    
    tools = ToolFramework()
      
    if args.new_session:
        messages = []
        print(f"Starting new session (cleared {args.session_file})")
    else:
        messages = load_session(args.session_file)
    
    if args.message:
        message = " ".join(args.message)
    else:
        print("Enter your message (Ctrl+D to finish):")
        message = sys.stdin.read().strip()
    
    if not message:
        print("Error: No message provided", file=sys.stderr)
        sys.exit(1)
    
    messages.append({
        "role": "user",
        "content": message
    })
    
    response = message_claude(messages)
    
    content = response["content"][0]["text"]
    
    content, tool_result = tools.parse_and_execute(content)
    print(content)
    messages.append({
        "role": "assistant", 
        "content": content
    })
    
    if tool_result:
        tool_summary = "Tool execution result:\n"
        tool_summary += tool_result
        
        messages.append({
            "role": "user",
            "content": f"[TOOL_RESULTS]\n{tool_summary}\n"
        })
        
        followup_response = message_claude(messages)
        followup_content = followup_response["content"][0]["text"]
        print(f"\n--- Claude's follow-up ---\n{followup_content}")
        
        messages.append({
            "role": "assistant",
            "content": followup_content
        })
    
    save_session(args.session_file, messages)

if __name__ == "__main__":
    main()