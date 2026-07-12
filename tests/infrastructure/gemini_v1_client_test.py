import httpx
import pytest

from simple_agent.infrastructure.gemini.gemini_v1_client import (
    GeminiV1ClientError,
    GeminiV1LLM,
)
from simple_agent.infrastructure.model_config import ModelConfig


@pytest.mark.asyncio
async def test_gemini_v1_chat_sends_api_key_as_header():
    response_data = {
        "candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]
    }
    captured = {}

    def handler(request):
        if "generateContent" in str(request.url):
            captured["url"] = str(request.url)
            captured["headers"] = request.headers
        return httpx.Response(200, json=response_data)

    transport = httpx.MockTransport(handler)
    chat = GeminiV1LLM(build_config(base_url=None), transport=transport)

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "assistant response"
    assert captured["headers"]["x-goog-api-key"] == "test-api-key"
    assert (
        captured["url"]
        == "https://generativelanguage.googleapis.com/v1/models/test-model:generateContent"
    )


def test_gemini_v1_chat_raises_error_when_adapter_is_not_gemini_v1():
    config = build_config(adapter="openai")

    with pytest.raises(GeminiV1ClientError) as error:
        GeminiV1LLM(config)

    assert (
        str(error.value)
        == "Configured adapter is not 'gemini_v1'; cannot use Gemini V1 client"
    )


def build_config(
    adapter: str = "gemini_v1",
    base_url: str | None = "https://generativelanguage.googleapis.com/v1",
) -> ModelConfig:
    return ModelConfig(
        name="gemini_v1",
        model="test-model",
        adapter=adapter,
        api_key="test-api-key",
        base_url=base_url,
        request_timeout=60,
    )
