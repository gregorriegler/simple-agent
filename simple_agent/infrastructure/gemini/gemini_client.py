import httpx

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.infrastructure.llm_http import post_with_retry
from simple_agent.infrastructure.logging_http_client import LoggingAsyncClient
from simple_agent.infrastructure.model_config import ModelConfig


class GeminiClientError(Exception):
    pass


class GeminiLLM(LLM):
    client_label = "Gemini client"
    adapter_name = "gemini"
    default_base_url = "https://generativelanguage.googleapis.com/v1beta"
    error_class: type[Exception] = GeminiClientError

    def __init__(
        self, config: ModelConfig, transport: httpx.AsyncBaseTransport | None = None
    ):
        self._config = config
        self._transport = transport
        self._ensure_adapter()
        self._input_token_limit = None

    async def _get_input_token_limit(self) -> int | None:
        if self._input_token_limit is not None:
            return self._input_token_limit

        api_key = self._config.api_key
        model = self._config.model
        base_url = self._base_url()
        url = f"{base_url.rstrip('/')}/models/{model}?key={api_key}"

        try:
            async with LoggingAsyncClient(
                timeout=10, transport=self._transport
            ) as client:
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

        url, headers = self._generate_content_request(self._base_url(), model, api_key)

        gemini_contents = self._convert_messages_to_gemini_format(messages)

        data = {
            "contents": gemini_contents,
        }

        response = await post_with_retry(
            url,
            headers=headers,
            json=data,
            timeout=self._config.request_timeout,
            error_class=self.error_class,
            transport=self._transport,
        )

        response_data = response.json()

        if "error" in response_data:
            error_message = response_data["error"].get("message", "Unknown error")
            error_code = response_data["error"].get("code", "")
            raise self.error_class(f"Gemini API error [{error_code}]: {error_message}")

        candidates = response_data.get("candidates")
        if not candidates:
            raise self.error_class("API response missing 'candidates' field")

        first_candidate = candidates[0]
        content = first_candidate.get("content")
        if content is None:
            raise self.error_class("API response missing 'content' field")

        parts = content.get("parts")
        if not parts:
            raise self.error_class("API response missing 'parts' field")

        text_parts = [part.get("text", "") for part in parts if "text" in part]
        text_content = "".join(text_parts)

        usage_metadata = response_data.get("usageMetadata", {})
        input_token_limit = await self._get_input_token_limit()

        usage = TokenUsage(
            input_tokens=usage_metadata.get("promptTokenCount", 0),
            output_tokens=usage_metadata.get("candidatesTokenCount", 0),
            total_tokens=usage_metadata.get("totalTokenCount", 0),
            input_token_limit=input_token_limit
            if input_token_limit and input_token_limit > 0
            else None,
        )

        return LLMResponse(content=text_content, model=model, usage=usage)

    def _base_url(self) -> str:
        return self._config.base_url or self.default_base_url

    def _generate_content_request(
        self, base_url: str, model: str, api_key: str
    ) -> tuple[str, dict[str, str]]:
        url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"
        return url, {"Content-Type": "application/json"}

    def _convert_messages_to_gemini_format(self, messages: ChatMessages) -> list[dict]:
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

                gemini_contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                gemini_contents.append({"role": "model", "parts": [{"text": content}]})

        return gemini_contents

    def _ensure_adapter(self) -> None:
        if self._config.adapter != self.adapter_name:
            raise self.error_class(
                f"Configured adapter is not '{self.adapter_name}'; "
                f"cannot use {self.client_label}"
            )
