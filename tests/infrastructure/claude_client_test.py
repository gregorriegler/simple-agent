import pytest
import httpx

from simple_agent.infrastructure.claude.claude_client import (
    ClaudeLLM,
    ClaudeClientError,
)


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

    chat = ClaudeLLM(StubClaudeConfig(), transport=transport)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Hello"},
    ]

    result = await chat.call_async(messages)

    assert result.content == "assistant response"
    assert result.model == "test-model"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


@pytest.mark.asyncio
async def test_claude_chat_raises_error_when_content_missing():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))

    chat = ClaudeLLM(StubClaudeConfig(), transport=transport)

    with pytest.raises(ClaudeClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


@pytest.mark.asyncio
async def test_claude_chat_raises_error_when_request_fails():
    def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    transport = httpx.MockTransport(handler)
    chat = ClaudeLLM(StubClaudeConfig(), transport=transport)

    with pytest.raises(ClaudeClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert "API request failed" in str(error.value)


class StubClaudeConfig:
    def __init__(self, base_url=None):
        self._base_url = base_url

    @property
    def api_key(self):
        return "test-api-key"

    @property
    def model(self):
        return "test-model"

    @property
    def adapter(self):
        return "claude"

    @property
    def base_url(self):
        return self._base_url

    @property
    def request_timeout(self):
        return 60
