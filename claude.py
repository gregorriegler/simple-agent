#!/usr/bin/env python

import requests
import json
import sys
import os
import argparse

def read_file(filename):
    """Read content from a file, handling errors gracefully."""
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filename}: {e}", file=sys.stderr)
        sys.exit(1)

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

def send_claude_request(api_key, model, messages, system_prompt=None):
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
    
    # Read API key and model from files
    api_key = read_file("claude-api-key.txt")
    model = read_file("claude-model.txt")
    
    # Read system prompt if file exists
    system_prompt = None
    if os.path.exists("system-prompt.txt"):
        system_prompt = read_file("system-prompt.txt")
    
    # Load or initialize session
    if args.new_session:
        messages = []
        print(f"Starting new session (cleared {args.session_file})")
    else:
        messages = load_session(args.session_file)
    
    # Get message from command line argument or stdin
    if args.message:
        message = " ".join(args.message)
    else:
        print("Enter your message (Ctrl+D to finish):")
        message = sys.stdin.read().strip()
    
    if not message:
        print("Error: No message provided", file=sys.stderr)
        sys.exit(1)
    
    # Add user message to conversation
    messages.append({
        "role": "user",
        "content": message
    })
    
    # Send request to Claude API
    response = send_claude_request(api_key, model, messages, system_prompt)
    
    # Extract and print the response content
    try:
        content = response["content"][0]["text"]
        print(content)
        
        # Add Claude's response to conversation history
        messages.append({
            "role": "assistant",
            "content": content
        })
        
        # Save updated session
        save_session(args.session_file, messages)
        
    except (KeyError, IndexError) as e:
        print(f"Error parsing response: {e}", file=sys.stderr)
        print(f"Raw response: {json.dumps(response, indent=2)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()