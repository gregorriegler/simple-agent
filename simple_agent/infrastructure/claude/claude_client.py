import logging

import httpx

from simple_agent.application.llm import (
    LLM,
    ChatMessages,
    LLMResponse,
    TokenUsage,
    split_system_prompt,
)
from simple_agent.application.tool_library import Tool
from simple_agent.infrastructure.claude.claude_messages import to_messages_api
from simple_agent.infrastructure.claude.claude_tools import to_tool_calls, to_tools
from simple_agent.infrastructure.llm_http import post_with_retry
from simple_agent.infrastructure.model_config import ModelConfig

logger = logging.getLogger(__name__)


class ClaudeClientError(RuntimeError):
    pass


class ClaudeLLM(LLM):
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
        self._ensure_claude_adapter()

    @property
    def model(self) -> str:
        return self._config.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        return await self._call_async(messages)

    async def _call_async(self, messages: ChatMessages) -> LLMResponse:
        base_url = self._config.base_url or "https://api.anthropic.com/v1"
        url = f"{base_url}/messages"
        api_key = self._config.api_key
        model = self._config.model
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        system_prompt, history = split_system_prompt(messages)
        data = {
            "model": model,
            "max_tokens": 4000,
            "messages": to_messages_api(history),
            **({"system": system_prompt} if system_prompt else {}),
        }
        if self._tools:
            data["tools"] = to_tools(self._tools)

        response = await post_with_retry(
            url,
            headers=headers,
            json=data,
            timeout=self._config.request_timeout,
            error_class=ClaudeClientError,
            transport=self._transport,
        )

        response_data = response.json()

        if "error" in response_data:
            error_type = response_data["error"].get("type", "")
            error_message = response_data["error"].get("message", "")
            raise ClaudeClientError(f"Claude API error: {error_type} - {error_message}")

        if "content" not in response_data:
            raise ClaudeClientError("API response missing 'content' field")

        content_list = response_data["content"]
        content = "".join(
            block.get("text", "")
            for block in content_list
            if block.get("type") == "text"
        )
        tool_calls = (
            to_tool_calls(content_list, self._declarations) if self._tools else []
        )

        usage_data = response_data.get("usage", {})
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        return LLMResponse(
            answer=content, tool_calls=tool_calls, model=model, usage=usage
        )

    def _ensure_claude_adapter(self) -> None:
        if self._config.adapter != "claude":
            raise ClaudeClientError(
                "Configured adapter is not 'claude'; cannot use Claude client"
            )
