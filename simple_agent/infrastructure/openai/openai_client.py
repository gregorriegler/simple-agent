import json
import logging
from typing import List, Dict

import requests

from simple_agent.application.llm import LLM, ChatMessages
from .openai_config import load_openai_config

logger = logging.getLogger(__name__)
logging.basicConfig(filename="request.log", encoding="utf-8", level=logging.DEBUG)


class OpenAIClientError(RuntimeError):
    pass


class OpenAILLM(LLM):
    def __init__(self, config=None):
        self._config = config or load_openai_config()

    def __call__(self, messages: ChatMessages) -> str:
        url = f"{self._config.base_url.rstrip('/')}/v1/chat/completions"
        api_key = self._config.api_key
        model = self._config.model

        payload_messages: List[Dict[str, str]] = list(messages)

        data = {
            "model": model,
            "messages": payload_messages,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        try:
            logger.debug("Request:" + json.dumps(data, indent=4, ensure_ascii=False))
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=self._config.request_timeout,
            )
            logger.debug("Response:" + json.dumps(response.json(), indent=4, ensure_ascii=False))
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            raise OpenAIClientError(f"API request failed: {error}") from error

        response_data = response.json()
        choices = response_data.get("choices")
        if not choices:
            raise OpenAIClientError("API response missing 'choices' field")

        message = choices[0].get("message")
        if not message or "content" not in message:
            raise OpenAIClientError("API response missing 'message.content' field")

        return message["content"] or ""
