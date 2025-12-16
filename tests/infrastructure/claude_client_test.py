import asyncio
import pytest
import respx
import httpx

from simple_agent.infrastructure.claude.claude_client import ClaudeLLM, ClaudeClientError


@respx.mock
def test_claude_chat_returns_content_text():
    response_data = {
        "content": [{"text": "assistant response"}],
        "usage": {
            "input_tokens": 10,
            "output_tokens": 20
        }
    }
    system_prompt = "system prompt"

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(200, json=response_data)
    )

    chat = ClaudeLLM(StubClaudeConfig())
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Hello"}
    ]

    result = asyncio.run(chat.call_async(messages))

    assert result.content == "assistant response"
    assert result.model == "test-model"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


@respx.mock
def test_claude_chat_raises_error_when_content_missing():
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(200, json={})
    )

    chat = ClaudeLLM(StubClaudeConfig())

    with pytest.raises(ClaudeClientError) as error:
        asyncio.run(chat.call_async([{"role": "user", "content": "Hello"}]))

    assert str(error.value) == "API response missing 'content' field"


@respx.mock
def test_claude_chat_raises_error_when_request_fails():
    respx.post("https://api.anthropic.com/v1/messages").mock(side_effect=httpx.ConnectError("Connection failed"))

    chat = ClaudeLLM(StubClaudeConfig())

    with pytest.raises(ClaudeClientError) as error:
        asyncio.run(chat.call_async([{"role": "user", "content": "Hello"}]))

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
