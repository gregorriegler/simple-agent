import json
import logging
from typing import Dict, List

import httpx

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.infrastructure.model_config import ModelConfig

logger = logging.getLogger(__name__)


class OpenAIClientError(RuntimeError):
    pass


class OpenAILLM(LLM):
    def __init__(self, config: ModelConfig):
        self._config = config
        self._ensure_openai_adapter()

    @property
    def model(self) -> str:
        return self._config.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        return await self._call_async(messages)

    async def _call_async(self, messages: ChatMessages) -> LLMResponse:
        base_url = self._config.base_url or "https://api.openai.com/v1"
        url = f"{base_url.rstrip('/')}/chat/completions"
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

        timeout = self._config.request_timeout

        try:
            logger.debug("Request:" + json.dumps(data, indent=4, ensure_ascii=False))
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=data)
            logger.debug(
                "Response:" + json.dumps(response.json(), indent=4, ensure_ascii=False)
            )
            response.raise_for_status()
        except httpx.RequestError as error:
            raise OpenAIClientError(f"API request failed: {error}") from error

        response_data = response.json()

        choices = response_data.get("choices")
        if not choices:
            raise OpenAIClientError("API response missing 'choices' field")

        message = choices[0].get("message")
        if not message or "content" not in message:
            raise OpenAIClientError("API response missing 'message.content' field")

        content = message["content"] or ""

        usage_data = response_data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return LLMResponse(content=content, model=model, usage=usage)

    def _ensure_openai_adapter(self) -> None:
        if self._config.adapter != "openai":
            raise OpenAIClientError(
                "Configured adapter is not 'openai'; cannot use OpenAI client"
            )
