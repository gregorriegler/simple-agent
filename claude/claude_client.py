import json
import logging
import requests

from .claude_config import claude_config
from message_exceptions import (
    ChatInterruptError,
    ChatRequestError,
    ChatResponseError,
)

logger = logging.getLogger(__name__)
logging.basicConfig(filename='request.log', encoding='utf-8', level=logging.DEBUG)


def chat(messages, system_prompt):
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
            raise ChatResponseError("API response missing 'content' field")

        content = response_data["content"]
        if not content:
            raise ChatResponseError("API response has empty content array")

        message = content[0]
        if "text" not in message:
            raise ChatResponseError("API response content missing 'text' field")

        return message["text"]
    except requests.exceptions.RequestException as e:
        raise ChatRequestError(f"API request failed: {e}") from e
    except KeyboardInterrupt as e:
        raise ChatInterruptError("Exiting...") from e
