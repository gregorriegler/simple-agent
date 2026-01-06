import httpx
import pytest

from simple_agent.infrastructure.gemini.gemini_client import (
    GeminiClientError,
    GeminiLLM,
)
from simple_agent.infrastructure.model_config import ModelConfig


@pytest.mark.asyncio
async def test_gemini_chat_returns_text_from_parts():
    response_data = {
        "candidates": [{"content": {"parts": [{"text": "assistant response"}]}}]
    }

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    chat = GeminiLLM(build_config(), transport=transport)
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

    chat = GeminiLLM(build_config(), transport=transport)
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

    chat = GeminiLLM(build_config(), transport=transport)
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

    chat = GeminiLLM(build_config(), transport=transport)
    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "First part. Second part."


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_candidates_missing():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))

    chat = GeminiLLM(build_config(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'candidates' field"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_content_missing():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"candidates": [{}]})
    )

    chat = GeminiLLM(build_config(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_parts_missing():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"candidates": [{"content": {}}]})
    )

    chat = GeminiLLM(build_config(), transport=transport)

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

    chat = GeminiLLM(build_config(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini API error [400]: Invalid API key"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_request_fails():
    def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    transport = httpx.MockTransport(handler)
    chat = GeminiLLM(build_config(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert "API request failed" in str(error.value)


def test_gemini_chat_raises_error_when_adapter_is_not_gemini():
    config = build_config(adapter="openai")

    with pytest.raises(GeminiClientError) as error:
        GeminiLLM(config)

    assert (
        str(error.value)
        == "Configured adapter is not 'gemini'; cannot use Gemini client"
    )


def build_config(
    adapter: str = "gemini",
    base_url: str | None = "https://generativelanguage.googleapis.com/v1beta",
) -> ModelConfig:
    return ModelConfig(
        name="gemini",
        model="test-model",
        adapter=adapter,
        api_key="test-api-key",
        base_url=base_url,
        request_timeout=60,
    )
