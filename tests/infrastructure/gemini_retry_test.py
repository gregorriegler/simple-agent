from unittest.mock import patch

import httpx
import pytest

from simple_agent.infrastructure.gemini.gemini_client import (
    GeminiClientError,
    GeminiLLM,
)
from simple_agent.infrastructure.model_config import ModelConfig

SUCCESS = {
    "status": "completed",
    "steps": [
        {"type": "model_output", "content": [{"type": "text", "text": "success"}]}
    ],
    "usage": {},
}


def build_config() -> ModelConfig:
    return ModelConfig(
        name="gemini",
        model="test-model",
        adapter="gemini",
        api_key="test-api-key",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        request_timeout=60,
    )


@pytest.mark.asyncio
async def test_gemini_retries_on_500():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(500)
        return httpx.Response(200, json=SUCCESS)

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))

    with patch("asyncio.sleep", return_value=None):
        result = await client.call_async([{"role": "user", "content": "hello"}])

    assert result.content == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_gemini_retries_on_timeout():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(200, json=SUCCESS)

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))

    with patch("asyncio.sleep", return_value=None):
        result = await client.call_async([{"role": "user", "content": "hello"}])

    assert result.content == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_gemini_eventually_fails_after_5_retries():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(500)

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(GeminiClientError) as excinfo:
            await client.call_async([{"role": "user", "content": "hello"}])

    assert call_count == 6
    assert "500" in str(excinfo.value)
