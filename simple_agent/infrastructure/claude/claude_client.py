import json
import logging

import requests

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.infrastructure.model_config import ModelConfig

logger = logging.getLogger(__name__)


class ClaudeClientError(RuntimeError):
    pass


class ClaudeLLM(LLM):
    def __init__(self, config: ModelConfig):
        self._config = config
        self._ensure_claude_adapter()

    @property
    def model(self) -> str:
        return self._config.model

    def __call__(self, messages: ChatMessages) -> LLMResponse:
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

        timeout = self._config.request_timeout

        try:
            logger.debug("Request:" + json.dumps(data, indent=4, ensure_ascii=False))
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
            logger.debug(
                "Response:" + json.dumps(response.json(), indent=4, ensure_ascii=False)
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            raise ClaudeClientError(f"API request failed: {error}") from error

        response_data = response.json()

        if "error" in response_data:
            error_type = response_data["error"].get("type", "")
            error_message = response_data["error"].get("message", "")
            raise ClaudeClientError(f"Claude API error: {error_type} - {error_message}")

        if "content" not in response_data:
            raise ClaudeClientError("API response missing 'content' field")

        content_list = response_data["content"]
        content = ""
        if content_list:
            first_content = content_list[0]
            if "text" not in first_content:
                raise ClaudeClientError("API response content missing 'text' field")
            content = first_content["text"]

        usage_data = response_data.get("usage", {})
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        return LLMResponse(content=content, model=model, usage=usage)

    def _ensure_claude_adapter(self) -> None:
        if self._config.adapter != "claude":
            raise ClaudeClientError(
                "Configured adapter is not 'claude'; cannot use Claude client"
            )
