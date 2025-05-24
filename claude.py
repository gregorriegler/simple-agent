#!/usr/bin/env python

import requests
import json
import sys
import os

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

def send_claude_request(api_key, model, message, system_prompt=None):
    """Send a request to the Claude API."""
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": model,
        "max_tokens": 4000,
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
    }
    
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
    # Read API key and model from files
    api_key = read_file("claude-api-key.txt")
    model = read_file("claude-model.txt")
    
    system_prompt = None
    if os.path.exists("system-prompt.txt"):
        system_prompt = read_file("system-prompt.txt")
    
    # Get message from command line argument or stdin
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        print("Enter your message (Ctrl+D to finish):")
        message = sys.stdin.read().strip()
    
    if not message:
        print("Error: No message provided", file=sys.stderr)
        sys.exit(1)
    
    # Send request to Claude API
    response = send_claude_request(api_key, model, message, system_prompt)
    
    # Extract and print the response content
    try:
        content = response["content"][0]["text"]
        print(content)
    except (KeyError, IndexError) as e:
        print(f"Error parsing response: {e}", file=sys.stderr)
        print(f"Raw response: {json.dumps(response, indent=2)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()