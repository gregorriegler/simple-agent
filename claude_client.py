import sys
import json
import requests
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='request.log', encoding='utf-8', level=logging.DEBUG)

def message_claude(messages, system_prompt):
    url = "https://api.anthropic.com/v1/messages"
    api_key = read_file("claude-api-key.txt")
    model = read_file("claude-model.txt")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    data = {
        "model": model,
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": messages
    }

    try:
        logger.debug("Request:" + json.dumps(data, indent=4))
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.debug("Response:" + json.dumps(response.json(), indent=4))
        return response.json()["content"][0]["text"]
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(1)

def read_file(filename):
    """Read content from a file, handling errors gracefully."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filename}: {e}", file=sys.stderr)
        sys.exit(1)
