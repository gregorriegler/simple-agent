from unittest.mock import patch

import httpx
import pytest

from simple_agent.infrastructure.claude.claude_client import (
    ClaudeClientError,
    ClaudeLLM,
)
from simple_agent.infrastructure.gemini.gemini_client import (
    GeminiClientError,
    GeminiLLM,
)
from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.infrastructure.openai.openai_client import (
    OpenAIClientError,
    OpenAILLM,
)

CLIENTS = [
    pytest.param(
        ClaudeLLM,
        ClaudeClientError,
        "claude",
        {"content": [{"text": "success"}]},
        id="claude",
    ),
    pytest.param(
        OpenAILLM,
        OpenAIClientError,
        "openai",
        {"choices": [{"message": {"content": "success"}}]},
        id="openai",
    ),
    pytest.param(
        GeminiLLM,
        GeminiClientError,
        "gemini",
        {
            "status": "completed",
            "steps": [
                {
                    "type": "model_output",
                    "content": [{"type": "text", "text": "success"}],
                }
            ],
        },
        id="gemini",
    ),
]


def build_config(adapter: str) -> ModelConfig:
    return ModelConfig(
        name=adapter,
        model="test-model",
        adapter=adapter,
        api_key="test-api-key",
        base_url=None,
        request_timeout=60,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("llm_class,error_class,adapter,success_json", CLIENTS)
async def test_client_wraps_http_status_error(
    llm_class, error_class, adapter, success_json
):
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    client = llm_class(build_config(adapter), transport=transport)

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(error_class) as error:
            await client.call_async([{"role": "user", "content": "Hello"}])

    assert "API request failed" in str(error.value)
    assert "500" in str(error.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("llm_class,error_class,adapter,success_json", CLIENTS)
async def test_client_retries_transient_500(
    llm_class, error_class, adapter, success_json
):
    post_count = 0

    def handler(request):
        nonlocal post_count
        post_count += 1
        if post_count < 3:
            return httpx.Response(500)
        return httpx.Response(200, json=success_json)

    transport = httpx.MockTransport(handler)
    client = llm_class(build_config(adapter), transport=transport)

    with patch("asyncio.sleep", return_value=None):
        result = await client.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "success"
    assert post_count == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("llm_class,error_class,adapter,success_json", CLIENTS)
async def test_client_surfaces_api_error_message(
    llm_class, error_class, adapter, success_json
):
    error_body = {
        "error": {
            "code": 400,
            "message": "API key not valid",
            "status": "INVALID_ARGUMENT",
        }
    }
    transport = httpx.MockTransport(
        lambda request: httpx.Response(400, json=error_body)
    )
    client = llm_class(build_config(adapter), transport=transport)

    with pytest.raises(error_class) as error:
        await client.call_async([{"role": "user", "content": "Hello"}])

    assert "API key not valid" in str(error.value)
    assert "INVALID_ARGUMENT" in str(error.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("llm_class,error_class,adapter,success_json", CLIENTS)
async def test_client_does_not_echo_an_unrecognized_error_body(
    llm_class, error_class, adapter, success_json
):
    """A gateway may echo the request, credentials included, so only a known
    error envelope is quoted back."""
    body = "<html>debug: x-goog-api-key: super-secret-key</html>"
    transport = httpx.MockTransport(lambda request: httpx.Response(400, text=body))
    client = llm_class(build_config(adapter), transport=transport)

    with pytest.raises(error_class) as error:
        await client.call_async([{"role": "user", "content": "Hello"}])

    assert "super-secret-key" not in str(error.value)
    assert "400" in str(error.value)
