import json
import logging

import requests

from simple_agent.application.llm import LLM, ChatMessages
from simple_agent.infrastructure.model_config import load_model_config, ModelConfig

logger = logging.getLogger(__name__)
logging.basicConfig(filename="request.log", encoding="utf-8", level=logging.DEBUG)


class ClaudeClientError(RuntimeError):
    pass


class ClaudeLLM(LLM):
    def __init__(self, config: ModelConfig | None = None):
        self._config = config or load_model_config()
        self._ensure_claude_adapter()

    def __call__(self, messages: ChatMessages) -> str:
        url = "https://api.anthropic.com/v1/messages"
        api_key = self._config.api_key
        model = self._config.model
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        payload_messages = list(messages)
        system_prompt = (
            payload_messages.pop(0).get("content", "")
            if payload_messages and payload_messages[0].get("role") == "system"
            else None
        )
        data = {
            "model": model,
            "max_tokens": 4000,
            "messages": payload_messages,
            **({"system": system_prompt} if system_prompt else {}),
        }
        try:
            logger.debug("Request:" + json.dumps(data, indent=4, ensure_ascii=False))
            response = requests.post(url, headers=headers, json=data)
            logger.debug(
                "Response:" + json.dumps(response.json(), indent=4, ensure_ascii=False)
            )
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
        except requests.exceptions.RequestException as error:
            raise ClaudeClientError(f"API request failed: {error}") from error

    def _ensure_claude_adapter(self) -> None:
        if self._config.adapter != "claude":
            raise ClaudeClientError(
                "Configured adapter is not 'claude'; cannot use Claude client"
            )
