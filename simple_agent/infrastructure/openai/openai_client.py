import logging

import httpx

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.application.tool_library import Tool
from simple_agent.infrastructure.llm_http import post_with_retry
from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.infrastructure.openai.openai_messages import (
    to_chat_completion_messages,
)
from simple_agent.infrastructure.openai.openai_tools import to_tool_calls, to_tools

logger = logging.getLogger(__name__)


class OpenAIClientError(RuntimeError):
    pass


class OpenAILLM(LLM):
    def __init__(
        self,
        config: ModelConfig,
        tools: list[Tool] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._config = config
        self._tools = tools or []
        self._declarations = {tool.name: tool for tool in self._tools}
        self._transport = transport
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

        data = {
            "model": model,
            "messages": to_chat_completion_messages(messages),
        }
        if self._tools:
            data["tools"] = to_tools(self._tools)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        response = await post_with_retry(
            url,
            headers=headers,
            json=data,
            timeout=self._config.request_timeout,
            error_class=OpenAIClientError,
            transport=self._transport,
        )

        response_data = response.json()

        choices = response_data.get("choices")
        if not choices:
            raise OpenAIClientError("API response missing 'choices' field")

        message = choices[0].get("message")
        if not message:
            raise OpenAIClientError("API response missing 'message' field")

        message_calls = message.get("tool_calls") or []
        tool_calls = (
            to_tool_calls(message_calls, self._declarations) if self._tools else []
        )
        if "content" not in message and not tool_calls:
            raise OpenAIClientError("API response missing 'message.content' field")

        content = message.get("content") or ""

        usage_data = response_data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return LLMResponse(
            answer=content, tool_calls=tool_calls, model=model, usage=usage
        )

    def _ensure_openai_adapter(self) -> None:
        if self._config.adapter != "openai":
            raise OpenAIClientError(
                "Configured adapter is not 'openai'; cannot use OpenAI client"
            )
