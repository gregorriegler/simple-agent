import pytest

from simple_agent.infrastructure.gemini.gemini_client import GeminiLLM, GeminiClientError


def test_gemini_chat_returns_text_from_parts(httpserver):
    response_data = {
        "candidates": [{
            "content": {
                "parts": [{"text": "assistant response"}]
            }
        }]
    }

    httpserver.expect_request(
        "/models/test-model:generateContent",
        method="POST",
        query_string="key=test-api-key",
        json={"contents": [{"role": "user", "parts": [{"text": "Hello"}]}]}
    ).respond_with_json(response_data)

    chat = GeminiLLM(StubGeminiConfig(base_url=httpserver.url_for("")))
    messages = [{"role": "user", "content": "Hello"}]

    result = chat(messages)

    assert result.content == "assistant response"
    assert result.model == "test-model"


def test_gemini_chat_handles_system_prompt(httpserver):
    response_data = {"candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]}

    httpserver.expect_request(
        "/models/test-model:generateContent",
        method="POST",
        query_string="key=test-api-key",
        json={"contents": [{"role": "user", "parts": [{"text": "You are a helpful assistant\n\nHello"}]}]}
    ).respond_with_json(response_data)

    chat = GeminiLLM(StubGeminiConfig(base_url=httpserver.url_for("")))
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"}
    ]

    result = chat(messages)

    assert result.content == "assistant response"


def test_gemini_chat_converts_assistant_to_model_role(httpserver):
    response_data = {"candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]}

    httpserver.expect_request(
        "/models/test-model:generateContent",
        method="POST",
        query_string="key=test-api-key",
        json={"contents": [
            {"role": "user", "parts": [{"text": "Hello"}]},
            {"role": "model", "parts": [{"text": "Hi there!"}]},
            {"role": "user", "parts": [{"text": "How are you?"}]}
        ]}
    ).respond_with_json(response_data)

    chat = GeminiLLM(StubGeminiConfig(base_url=httpserver.url_for("")))
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]

    result = chat(messages)

    assert result.content == "assistant response"


def test_gemini_chat_concatenates_multiple_text_parts(httpserver):
    response_data = {"candidates": [{"content": {"parts": [
        {"text": "First part. "},
        {"text": "Second part."}
    ]}}]}

    httpserver.expect_request(
        "/models/test-model:generateContent",
        method="POST",
        query_string="key=test-api-key"
    ).respond_with_json(response_data)

    chat = GeminiLLM(StubGeminiConfig(base_url=httpserver.url_for("")))
    result = chat([{"role": "user", "content": "Hello"}])

    assert result.content == "First part. Second part."


def test_gemini_chat_raises_error_when_candidates_missing(httpserver):
    httpserver.expect_request(
        "/models/test-model:generateContent",
        method="POST",
        query_string="key=test-api-key"
    ).respond_with_json({})

    chat = GeminiLLM(StubGeminiConfig(base_url=httpserver.url_for("")))

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'candidates' field"


def test_gemini_chat_raises_error_when_content_missing(httpserver):
    httpserver.expect_request(
        "/models/test-model:generateContent",
        method="POST",
        query_string="key=test-api-key"
    ).respond_with_json({"candidates": [{}]})

    chat = GeminiLLM(StubGeminiConfig(base_url=httpserver.url_for("")))

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


def test_gemini_chat_raises_error_when_parts_missing(httpserver):
    httpserver.expect_request(
        "/models/test-model:generateContent",
        method="POST",
        query_string="key=test-api-key"
    ).respond_with_json({"candidates": [{"content": {}}]})

    chat = GeminiLLM(StubGeminiConfig(base_url=httpserver.url_for("")))

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'parts' field"


def test_gemini_chat_raises_error_on_api_error_response(httpserver):
    httpserver.expect_request(
        "/models/test-model:generateContent",
        method="POST",
        query_string="key=test-api-key"
    ).respond_with_json({"error": {"code": 400, "message": "Invalid API key"}})

    chat = GeminiLLM(StubGeminiConfig(base_url=httpserver.url_for("")))

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini API error [400]: Invalid API key"


def test_gemini_chat_raises_error_when_request_fails():
    chat = GeminiLLM(StubGeminiConfig(base_url="http://localhost:1"))

    with pytest.raises(GeminiClientError) as error:
        chat([{"role": "user", "content": "Hello"}])

    assert "API request failed" in str(error.value)


def test_gemini_chat_raises_error_when_adapter_is_not_gemini():
    config = StubGeminiConfig()
    config._adapter = "openai"

    with pytest.raises(GeminiClientError) as error:
        GeminiLLM(config)

    assert str(error.value) == "Configured adapter is not 'gemini'; cannot use Gemini client"


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
