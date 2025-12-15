import pytest

from simple_agent.infrastructure.claude.claude_client import ClaudeLLM, ClaudeClientError


def test_claude_chat_returns_content_text(httpserver):
    response_data = {
        "content": [{"text": "assistant response"}],
        "usage": {
            "input_tokens": 10,
            "output_tokens": 20
        }
    }
    system_prompt = "system prompt"

    httpserver.expect_request(
        "/messages",
        method="POST",
        json={
            "model": "test-model",
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": "Hello"}]
        },
        headers={
            "x-api-key": "test-api-key",
            "anthropic-version": "2023-06-01",
        }
    ).respond_with_json(response_data)

    chat = ClaudeLLM(StubClaudeConfig(base_url=httpserver.url_for("")))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Hello"}
    ]

    result = chat(messages)

    assert result.content == "assistant response"
    assert result.model == "test-model"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


def test_claude_chat_raises_error_when_content_missing(httpserver):
    httpserver.expect_request("/messages", method="POST").respond_with_json({})

    chat = ClaudeLLM(StubClaudeConfig(base_url=httpserver.url_for("")))

    with pytest.raises(ClaudeClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


def test_claude_chat_raises_error_when_request_fails(httpserver):
    # Don't set up any handler - connection will fail
    chat = ClaudeLLM(StubClaudeConfig(base_url="http://localhost:1"))

    with pytest.raises(ClaudeClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

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
