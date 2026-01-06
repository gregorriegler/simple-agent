import asyncio
import httpx
from typing import Dict, List

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.infrastructure.logging_http_client import LoggingAsyncClient


class GeminiClientError(Exception):
    pass


class GeminiLLM(LLM):
    def __init__(self, config: ModelConfig, transport: httpx.AsyncBaseTransport | None = None):
        self._config = config
        self._transport = transport
        self._ensure_gemini_adapter()
        self._input_token_limit = None

    async def _get_input_token_limit(self) -> int | None:
        if self._input_token_limit is not None:
            return self._input_token_limit

        api_key = self._config.api_key
        model = self._config.model
        base_url = self._config.base_url or "https://generativelanguage.googleapis.com/v1beta"
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

        base_url = self._config.base_url or "https://generativelanguage.googleapis.com/v1beta"
        url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"

        # Convert messages to Gemini format
        gemini_contents = self._convert_messages_to_gemini_format(messages)

        data = {
            "contents": gemini_contents,
        }

        headers = {
            "Content-Type": "application/json",
        }

        timeout = self._config.request_timeout
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries + 1):
            try:
                async with LoggingAsyncClient(timeout=timeout, transport=self._transport) as client:
                    response = await client.post(url, headers=headers, json=data)
                
                response.raise_for_status()
                break
            except (httpx.RequestError, httpx.HTTPStatusError) as error:
                should_retry = attempt < max_retries and (
                    isinstance(error, httpx.TimeoutException) or 
                    (isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 500)
                )
                
                if should_retry:
                    await asyncio.sleep(retry_delay)
                    continue
                
                raise GeminiClientError(f"API request failed: {error}") from error

        response_data = response.json()

        # Handle error responses
        if "error" in response_data:
            error_message = response_data["error"].get("message", "Unknown error")
            error_code = response_data["error"].get("code", "")
            raise GeminiClientError(f"Gemini API error [{error_code}]: {error_message}")

        # Extract response text
        candidates = response_data.get("candidates")
        if not candidates:
            raise GeminiClientError("API response missing 'candidates' field")

        first_candidate = candidates[0]
        content = first_candidate.get("content")
        if content is None:
            raise GeminiClientError("API response missing 'content' field")

        parts = content.get("parts")
        if not parts:
            raise GeminiClientError("API response missing 'parts' field")

        # Concatenate all text parts
        text_parts = [part.get("text", "") for part in parts if "text" in part]
        text_content = "".join(text_parts)

        # Gemini usage data extraction (if available, otherwise 0)
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
                # Store system prompt to prepend to first user message
                system_prompt = content
            elif role == "user":
                # Prepend system prompt if it exists
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

    def _ensure_gemini_adapter(self) -> None:
        if self._config.adapter != "gemini":
            raise GeminiClientError(
                "Configured adapter is not 'gemini'; cannot use Gemini client"
            )
