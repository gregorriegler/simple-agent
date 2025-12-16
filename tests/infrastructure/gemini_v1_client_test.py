import pytest
import re
import respx
import httpx

from simple_agent.infrastructure.gemini.gemini_v1_client import GeminiV1LLM, GeminiV1ClientError


@respx.mock
def test_gemini_v1_chat_returns_text_from_parts():
    response_data = {
        "candidates": [{
            "content": {
                "parts": [{"text": "assistant response"}]
            }
        }]
    }

    respx.post(re.compile(r"https://generativelanguage\.googleapis\.com/v1/models/test-model:generateContent.*")).mock(
        return_value=httpx.Response(200, json=response_data)
    )

    chat = GeminiV1LLM(StubGeminiV1Config())
    messages = [{"role": "user", "content": "Hello"}]

    result = chat(messages)

    assert result.content == "assistant response"
    assert result.model == "test-model"


@respx.mock
def test_gemini_v1_chat_handles_system_prompt():
    response_data = {"candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]}

    respx.post(re.compile(r"https://generativelanguage.googleapis.com/v1/models/test-model:generateContent.*")).mock(
        return_value=httpx.Response(200, json=response_data)
    )

    chat = GeminiV1LLM(StubGeminiV1Config())
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"}
    ]

    result = chat(messages)

    assert result.content == "assistant response"


@respx.mock
def test_gemini_v1_chat_converts_assistant_to_model_role():
    response_data = {"candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]}

    respx.post(re.compile(r"https://generativelanguage.googleapis.com/v1/models/test-model:generateContent.*")).mock(
        return_value=httpx.Response(200, json=response_data)
    )

    chat = GeminiV1LLM(StubGeminiV1Config())
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]

    result = chat(messages)

    assert result.content == "assistant response"


@respx.mock
def test_gemini_v1_chat_concatenates_multiple_text_parts():
    response_data = {"candidates": [{"content": {"parts": [
        {"text": "First part. "},
        {"text": "Second part."}
    ]}}]}

    respx.post(re.compile(r"https://generativelanguage.googleapis.com/v1/models/test-model:generateContent.*")).mock(
        return_value=httpx.Response(200, json=response_data)
    )

    chat = GeminiV1LLM(StubGeminiV1Config())
    result = chat([{"role": "user", "content": "Hello"}])

    assert result.content == "First part. Second part."


@respx.mock
def test_gemini_v1_chat_raises_error_when_candidates_missing():
    respx.post(re.compile(r"https://generativelanguage.googleapis.com/v1/models/test-model:generateContent.*")).mock(
        return_value=httpx.Response(200, json={})
    )

    chat = GeminiV1LLM(StubGeminiV1Config())

    with pytest.raises(GeminiV1ClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'candidates' field"


@respx.mock
def test_gemini_v1_chat_raises_error_when_content_missing():
    respx.post(re.compile(r"https://generativelanguage.googleapis.com/v1/models/test-model:generateContent.*")).mock(
        return_value=httpx.Response(200, json={"candidates": [{}]})
    )

    chat = GeminiV1LLM(StubGeminiV1Config())

    with pytest.raises(GeminiV1ClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


@respx.mock
def test_gemini_v1_chat_raises_error_when_parts_missing():
    respx.post(re.compile(r"https://generativelanguage.googleapis.com/v1/models/test-model:generateContent.*")).mock(
        return_value=httpx.Response(200, json={"candidates": [{"content": {}}]})
    )

    chat = GeminiV1LLM(StubGeminiV1Config())

    with pytest.raises(GeminiV1ClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'parts' field"


@respx.mock
def test_gemini_v1_chat_raises_error_on_api_error_response():
    respx.post(re.compile(r"https://generativelanguage.googleapis.com/v1/models/test-model:generateContent.*")).mock(
        return_value=httpx.Response(200, json={"error": {"code": 400, "message": "Invalid API key"}})
    )

    chat = GeminiV1LLM(StubGeminiV1Config())

    with pytest.raises(GeminiV1ClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini API error [400]: Invalid API key"


@respx.mock
def test_gemini_v1_chat_raises_error_when_request_fails():
    respx.post(re.compile(r"https://generativelanguage.googleapis.com/v1/models/test-model:generateContent.*")).mock(
        side_effect=httpx.ConnectError("Connection failed")
    )

    chat = GeminiV1LLM(StubGeminiV1Config())

    with pytest.raises(GeminiV1ClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert "API request failed" in str(error.value)


def test_gemini_v1_chat_raises_error_when_adapter_is_not_gemini_v1():
    config = StubGeminiV1Config()
    config._adapter = "openai"

    with pytest.raises(GeminiV1ClientError) as error:
        GeminiV1LLM(config)

    assert str(error.value) == "Configured adapter is not 'gemini_v1'; cannot use Gemini V1 client"


class StubGeminiV1Config:
    def __init__(self, base_url=None):
        self._base_url = base_url
        self._adapter = "gemini_v1"

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