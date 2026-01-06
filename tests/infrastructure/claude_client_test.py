import httpx
import pytest

from simple_agent.infrastructure.claude.claude_client import (
    ClaudeClientError,
    ClaudeLLM,
)
from simple_agent.infrastructure.model_config import ModelConfig


@pytest.mark.asyncio
async def test_claude_chat_returns_content_text():
    response_data = {
        "content": [{"text": "assistant response"}],
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    system_prompt = "system prompt"

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    chat = ClaudeLLM(build_config(), transport=transport)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Hello"},
    ]

    result = await chat.call_async(messages)

    assert result.content == "assistant response"
    assert result.model == "test-model"
    assert result.usage is not None
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


@pytest.mark.asyncio
async def test_claude_chat_raises_error_when_content_missing():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))

    chat = ClaudeLLM(build_config(), transport=transport)

    with pytest.raises(ClaudeClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


@pytest.mark.asyncio
async def test_claude_chat_raises_error_when_request_fails():
    def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    transport = httpx.MockTransport(handler)
    chat = ClaudeLLM(build_config(), transport=transport)

    with pytest.raises(ClaudeClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert "API request failed" in str(error.value)


def build_config(base_url: str | None = None) -> ModelConfig:
    return ModelConfig(
        name="claude",
        model="test-model",
        adapter="claude",
        api_key="test-api-key",
        base_url=base_url,
        request_timeout=60,
    )
