import pytest
import requests

from simple_agent.infrastructure.claude import claude_client
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM, ClaudeClientError
from simple_agent.infrastructure.claude.claude_config import claude_config


def test_claude_chat_returns_content_text(monkeypatch):
    stub_claude_config(monkeypatch)
    captured = {}
    monkeypatch.setattr(claude_client.requests, "post", create_successful_post(captured))
    chat = ClaudeLLM()
    system_prompt = "system prompt"
    messages = [{"role": "user", "content": "Hello"}]

    result = chat(system_prompt, messages)

    assert result == "assistant response"
    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"] == {
        "Content-Type": "application/json",
        "x-api-key": "test-api-key",
        "anthropic-version": "2023-06-01"
    }
    assert captured["json"] == {
        "model": "test-model",
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": messages
    }


def test_claude_chat_raises_error_when_content_missing(monkeypatch):
    stub_claude_config(monkeypatch)
    monkeypatch.setattr(claude_client.requests, "post", create_missing_content_post())
    chat = ClaudeLLM()

    with pytest.raises(ClaudeClientError) as error:
        chat("system", [])

    assert str(error.value) == "API response missing 'content' field"


def test_claude_chat_raises_error_when_request_fails(monkeypatch):
    stub_claude_config(monkeypatch)
    monkeypatch.setattr(claude_client.requests, "post", create_failing_post())
    chat = ClaudeLLM()

    with pytest.raises(ClaudeClientError) as error:
        chat("system", [])

    assert str(error.value) == "API request failed: network down"


def stub_claude_config(monkeypatch):
    test_config = {
        'claude': {
            'api_key': 'test-api-key',
            'model': 'test-model'
        }
    }
    monkeypatch.setattr(claude_config, "_config", test_config)


def create_successful_post(captured):
    response = ResponseStub({"content": [{"text": "assistant response"}]})

    def post(url, headers, json):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return response

    return post


def create_missing_content_post():
    response = ResponseStub({})

    def post(url, headers, json):
        return response

    return post


def create_failing_post():
    def post(url, headers, json):
        raise requests.exceptions.RequestException("network down")

    return post


class ResponseStub:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None
