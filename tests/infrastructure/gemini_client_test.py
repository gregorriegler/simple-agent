import httpx
import pytest

from simple_agent.infrastructure.gemini.gemini_client import (
    GeminiClientError,
    GeminiLLM,
)


@pytest.mark.asyncio
async def test_gemini_chat_returns_text_from_parts():
    response_data = {
        "candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]
    }

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    chat = GeminiLLM(StubGeminiConfig(), transport=transport)
    messages = [{"role": "user", "content": "Hello"}]

    result = await chat.call_async(messages)

    assert result.content == "assistant response"
    assert result.model == "test-model"


@pytest.mark.asyncio
async def test_gemini_chat_handles_system_prompt():
    response_data = {
        "candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]
    }

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    chat = GeminiLLM(StubGeminiConfig(), transport=transport)
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ]

    result = await chat.call_async(messages)

    assert result.content == "assistant response"


@pytest.mark.asyncio
async def test_gemini_chat_converts_assistant_to_model_role():
    response_data = {
        "candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]
    }

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    chat = GeminiLLM(StubGeminiConfig(), transport=transport)
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]

    result = await chat.call_async(messages)

    assert result.content == "assistant response"


@pytest.mark.asyncio
async def test_gemini_chat_concatenates_multiple_text_parts():
    response_data = {
        "candidates": [
            {"content": {"parts": [{"text": "First part. "}, {"text": "Second part."}]}}
        ]
    }

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    chat = GeminiLLM(StubGeminiConfig(), transport=transport)
    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "First part. Second part."


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_candidates_missing():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))

    chat = GeminiLLM(StubGeminiConfig(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'candidates' field"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_content_missing():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"candidates": [{}]})
    )

    chat = GeminiLLM(StubGeminiConfig(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_parts_missing():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"candidates": [{"content": {}}]})
    )

    chat = GeminiLLM(StubGeminiConfig(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'parts' field"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_on_api_error_response():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"error": {"code": 400, "message": "Invalid API key"}}
        )
    )

    chat = GeminiLLM(StubGeminiConfig(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini API error [400]: Invalid API key"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_request_fails():
    def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    transport = httpx.MockTransport(handler)
    chat = GeminiLLM(StubGeminiConfig(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert "API request failed" in str(error.value)


def test_gemini_chat_raises_error_when_adapter_is_not_gemini():
    config = StubGeminiConfig()
    config._adapter = "openai"

    with pytest.raises(GeminiClientError) as error:
        GeminiLLM(config)

    assert (
        str(error.value)
        == "Configured adapter is not 'gemini'; cannot use Gemini client"
    )


class StubGeminiConfig:
    def __init__(self, base_url="https://generativelanguage.googleapis.com/v1beta"):
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
