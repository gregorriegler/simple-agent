import json
import logging
import requests

from application.chat import Chat, ChatMessages
from .claude_config import claude_config

logger = logging.getLogger(__name__)
logging.basicConfig(filename='request.log', encoding='utf-8', level=logging.DEBUG)


class ClaudeClientError(RuntimeError):

    pass


class ClaudeChat(Chat):

    def __call__(self, system_prompt: str, messages: ChatMessages) -> str:
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
            logger.debug("Response:" + json.dumps(response.json(), indent=4))
            response.raise_for_status()
            response_data = response.json()
            if "content" not in response_data:
                raise ClaudeClientError("API response missing 'content' field")
            content = response_data["content"]
            if not content:
                return ""
            first_content = content[0]
            if "text" not in first_content:
                raise ClaudeClientError("API response content missing 'text' field")
            return first_content["text"]
        except requests.exceptions.RequestException as e:
            raise ClaudeClientError(f"API request failed: {e}") from e

