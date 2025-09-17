import sys
import json
import requests
import logging
from .claude_config import claude_config

logger = logging.getLogger(__name__)
logging.basicConfig(filename='request.log', encoding='utf-8', level=logging.DEBUG)

def chat(system_prompt, messages):
    url = "https://api.anthropic.com/v1/messages"
    api_key = claude_config.api_key
    model = claude_config.model

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

        response_data = response.json()
        if "content" not in response_data:
            print("API response missing 'content' field", file=sys.stderr)
            sys.exit(1)

        content = response_data["content"]
        if not content or len(content) == 0:
            print("API response has empty content array", file=sys.stderr)
            sys.exit(1)

        if "text" not in content[0]:
            print("API response content missing 'text' field", file=sys.stderr)
            sys.exit(1)

        return content[0]["text"]
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(1)

