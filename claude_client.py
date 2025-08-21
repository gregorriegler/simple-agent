import requests


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
        "messages": messages
    }

    if system_prompt is not None:
        data["system"] = system_prompt

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
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
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filename}: {e}", file=sys.stderr)
        sys.exit(1)
