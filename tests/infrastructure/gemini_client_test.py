import pytest
import requests

from simple_agent.infrastructure.gemini import gemini_client
from simple_agent.infrastructure.gemini.gemini_client import GeminiLLM, GeminiClientError


def test_gemini_chat_returns_text_from_parts(monkeypatch):
    captured = {}
    monkeypatch.setattr(gemini_client.requests, "post", create_successful_post(captured))
    chat = GeminiLLM(StubGeminiConfig())
    messages = [
        {"role": "user", "content": "Hello"}
    ]

    result = chat(messages)

    assert result == "assistant response"
    expected_url = "https://generativelanguage.googleapis.com/v1beta/models/test-model:generateContent?key=test-api-key"
    assert captured["url"] == expected_url
    assert captured["headers"] == {
        "Content-Type": "application/json",
    }
    assert captured["json"] == {
        "contents": [
            {"role": "user", "parts": [{"text": "Hello"}]}
        ]
    }
    assert captured["timeout"] == 60


def test_gemini_chat_handles_system_prompt(monkeypatch):
    captured = {}
    monkeypatch.setattr(gemini_client.requests, "post", create_successful_post(captured))
    chat = GeminiLLM(StubGeminiConfig())
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"}
    ]

    result = chat(messages)

    assert result == "assistant response"
    # System prompt should be prepended to first user message
    assert captured["json"]["contents"] == [
        {"role": "user", "parts": [{"text": "You are a helpful assistant\n\nHello"}]}
    ]


def test_gemini_chat_converts_assistant_to_model_role(monkeypatch):
    captured = {}
    monkeypatch.setattr(gemini_client.requests, "post", create_successful_post(captured))
    chat = GeminiLLM(StubGeminiConfig())
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]

    result = chat(messages)

    assert result == "assistant response"
    # Assistant role should be converted to 'model' for Gemini
    assert captured["json"]["contents"] == [
        {"role": "user", "parts": [{"text": "Hello"}]},
        {"role": "model", "parts": [{"text": "Hi there!"}]},
        {"role": "user", "parts": [{"text": "How are you?"}]}
    ]


def test_gemini_chat_respects_base_url_override(monkeypatch):
    captured = {}
    monkeypatch.setattr(gemini_client.requests, "post", create_successful_post(captured))
    custom_base_url = "https://custom-gemini-endpoint.com/api"
    chat = GeminiLLM(StubGeminiConfig(base_url=custom_base_url))
    messages = [{"role": "user", "content": "Hello"}]

    result = chat(messages)

    assert result == "assistant response"
    expected_url = f"{custom_base_url}/models/test-model:generateContent?key=test-api-key"
    assert captured["url"] == expected_url


def test_gemini_chat_concatenates_multiple_text_parts(monkeypatch):
    response_data = {
        "candidates": [{
            "content": {
                "parts": [
                    {"text": "First part. "},
                    {"text": "Second part."}
                ]
            }
        }]
    }
    monkeypatch.setattr(gemini_client.requests, "post", create_post_with_response(response_data))
    chat = GeminiLLM(StubGeminiConfig())

    result = chat([{"role": "user", "content": "Hello"}])

    assert result == "First part. Second part."


def test_gemini_chat_raises_error_when_candidates_missing(monkeypatch):
    monkeypatch.setattr(gemini_client.requests, "post", create_missing_candidates_post())
    chat = GeminiLLM(StubGeminiConfig())

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'candidates' field"


def test_gemini_chat_raises_error_when_content_missing(monkeypatch):
    response_data = {"candidates": [{}]}
    monkeypatch.setattr(gemini_client.requests, "post", create_post_with_response(response_data))
    chat = GeminiLLM(StubGeminiConfig())

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


def test_gemini_chat_raises_error_when_parts_missing(monkeypatch):
    response_data = {"candidates": [{"content": {}}]}
    monkeypatch.setattr(gemini_client.requests, "post", create_post_with_response(response_data))
    chat = GeminiLLM(StubGeminiConfig())

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'parts' field"


def test_gemini_chat_raises_error_on_api_error_response(monkeypatch):
    response_data = {
        "error": {
            "code": 400,
            "message": "Invalid API key"
        }
    }
    monkeypatch.setattr(gemini_client.requests, "post", create_post_with_response(response_data))
    chat = GeminiLLM(StubGeminiConfig())

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini API error [400]: Invalid API key"


def test_gemini_chat_raises_error_when_request_fails(monkeypatch):
    monkeypatch.setattr(gemini_client.requests, "post", create_failing_post())
    chat = GeminiLLM(StubGeminiConfig())

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API request failed: network down"


def test_gemini_chat_raises_error_when_adapter_is_not_gemini():
    config = StubGeminiConfig()
    config._adapter = "openai"  # Wrong adapter

    with pytest.raises(GeminiClientError) as error:
        GeminiLLM(config)

    assert str(error.value) == "Configured adapter is not 'gemini'; cannot use Gemini client"


def create_successful_post(captured):
    response_data = {
        "candidates": [{
            "content": {
                "parts": [{"text": "assistant response"}]
            }
        }]
    }
    response = ResponseStub(response_data)

    def post(url, headers, json, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return response

    return post


def create_post_with_response(response_data):
    response = ResponseStub(response_data)

    def post(url, headers, json, timeout=None):
        return response

    return post


def create_missing_candidates_post():
    response = ResponseStub({})

    def post(url, headers, json, timeout=None):
        return response

    return post


def create_failing_post():
    def post(url, headers, json, timeout=None):
        raise requests.exceptions.RequestException("network down")
    return post


class ResponseStub:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


class StubGeminiConfig:
    def __init__(self, base_url=None):
        self._base_url = base_url
        self._adapter = "gemini"

    @property
    def api_key(self):
        return "test-api-key"

    @property
    def model(self):
        return "test-model"

    @property
    def adapter(self):
        return self._adapter

    @property
    def base_url(self):
        return self._base_url

    @property
    def request_timeout(self):
        return 60
