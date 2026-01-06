import asyncio
import httpx
from typing import Dict, List

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.infrastructure.logging_http_client import LoggingAsyncClient


class GeminiV1ClientError(Exception):
    pass


class GeminiV1LLM(LLM):
    def __init__(self, config: ModelConfig, transport: httpx.AsyncBaseTransport | None = None):
        self._config = config
        self._transport = transport
        self._ensure_gemini_v1_adapter()
        self._input_token_limit = None

    async def _get_input_token_limit(self) -> int | None:
        if self._input_token_limit is not None:
            return self._input_token_limit

        api_key = self._config.api_key
        model = self._config.model
        base_url = self._config.base_url or "https://generativelanguage.googleapis.com/v1"
        url = f"{base_url.rstrip('/')}/models/{model}?key={api_key}"

        try:
            async with LoggingAsyncClient(timeout=10, transport=self._transport) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                self._input_token_limit = int(data.get("inputTokenLimit", 0))
        except Exception:
            self._input_token_limit = 0

        return self._input_token_limit

    @property
    def model(self) -> str:
        return self._config.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        return await self._call_async(messages)

    async def _call_async(self, messages: ChatMessages) -> LLMResponse:
        api_key = self._config.api_key
        model = self._config.model

        base_url = self._config.base_url or "https://generativelanguage.googleapis.com/v1"
        url = f"{base_url.rstrip('/')}/models/{model}:generateContent"

        gemini_contents = self._convert_messages_to_gemini_format(messages)

        data = {
            "contents": gemini_contents,
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

        timeout = self._config.request_timeout

        try:
            async with LoggingAsyncClient(timeout=timeout, transport=self._transport) as client:
                response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
        except httpx.RequestError as error:
            raise GeminiV1ClientError(f"API request failed: {error}") from error

        response_data = response.json()

        if "error" in response_data:
            error_message = response_data["error"].get("message", "Unknown error")
            error_code = response_data["error"].get("code", "")
            raise GeminiV1ClientError(f"Gemini API error [{error_code}]: {error_message}")

        candidates = response_data.get("candidates")
        if not candidates:
            raise GeminiV1ClientError("API response missing 'candidates' field")

        first_candidate = candidates[0]
        content = first_candidate.get("content")
        if content is None:
            raise GeminiV1ClientError("API response missing 'content' field")

        parts = content.get("parts")
        if not parts:
            raise GeminiV1ClientError("API response missing 'parts' field")

        text_parts = [part.get("text", "") for part in parts if "text" in part]
        text_content = "".join(text_parts)

        usage_metadata = response_data.get("usageMetadata", {})
        input_token_limit = await self._get_input_token_limit()

        usage = TokenUsage(
            input_tokens=usage_metadata.get("promptTokenCount", 0),
            output_tokens=usage_metadata.get("candidatesTokenCount", 0),
            total_tokens=usage_metadata.get("totalTokenCount", 0),
            input_token_limit=input_token_limit if input_token_limit and input_token_limit > 0 else None
        )

        return LLMResponse(content=text_content, model=model, usage=usage)

    def _convert_messages_to_gemini_format(self, messages: ChatMessages) -> List[Dict]:
        """
        Convert standard chat messages to Gemini API format.

        Gemini expects:
        - 'user' role for user messages
        - 'model' role for assistant messages
        - System messages are not directly supported, so we prepend them to the first user message
        """
        gemini_contents = []
        system_prompt = None

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "system":
                system_prompt = content
            elif role == "user":
                if system_prompt:
                    content = f"{system_prompt}\n\n{content}"
                    system_prompt = None

                gemini_contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant":
                gemini_contents.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })

        return gemini_contents

    def _ensure_gemini_v1_adapter(self) -> None:
        if self._config.adapter != "gemini_v1":
            raise GeminiV1ClientError(
                "Configured adapter is not 'gemini_v1'; cannot use Gemini V1 client"
            )
