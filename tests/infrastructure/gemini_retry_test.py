from unittest.mock import patch

import httpx
import pytest

from simple_agent.infrastructure.gemini.gemini_client import (
    GeminiClientError,
    GeminiLLM,
)


class StubGeminiConfig:
    def __init__(self):
        self.api_key = "test-api-key"
        self.model = "test-model"
        self.adapter = "gemini"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.request_timeout = 60


@pytest.mark.asyncio
async def test_gemini_retries_on_500():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1

        # Handle model metadata call (happens after main call succeeds)
        if "models/" in str(request.url) and "generateContent" not in str(request.url):
            return httpx.Response(200, json={"inputTokenLimit": 1000000})

        # Handle main API call with retries
        if call_count < 3:
            return httpx.Response(500)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "success"}]}}],
                "usageMetadata": {},
            },
        )

    transport = httpx.MockTransport(handler)
    client = GeminiLLM(StubGeminiConfig(), transport=transport)

    # We need to patch asyncio.sleep to avoid waiting in tests
    with patch("asyncio.sleep", return_value=None):
        result = await client.call_async([{"role": "user", "content": "hello"}])

    assert result.content == "success"
    # 2 failures (500) + 1 success (main call) + 1 model metadata call = 4 total
    assert call_count == 4


@pytest.mark.asyncio
async def test_gemini_retries_on_timeout():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1

        # Handle model metadata call (happens after main call succeeds)
        if "models/" in str(request.url) and "generateContent" not in str(request.url):
            return httpx.Response(200, json={"inputTokenLimit": 1000000})

        # Handle main API call with timeout retry
        if call_count < 2:
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "success"}]}}],
                "usageMetadata": {},
            },
        )

    transport = httpx.MockTransport(handler)
    client = GeminiLLM(StubGeminiConfig(), transport=transport)

    with patch("asyncio.sleep", return_value=None):
        result = await client.call_async([{"role": "user", "content": "hello"}])

    assert result.content == "success"
    # 1 timeout + 1 success (main call) + 1 model metadata call = 3 total
    assert call_count == 3


@pytest.mark.asyncio
async def test_gemini_eventually_fails_after_5_retries():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        # Always return 500 for both main API and metadata calls
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    client = GeminiLLM(StubGeminiConfig(), transport=transport)

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(GeminiClientError) as excinfo:
            await client.call_async([{"role": "user", "content": "hello"}])

    # Initial call + 5 retries = 6 calls total (metadata call not attempted since main call fails)
    assert call_count == 6
    assert "500" in str(excinfo.value)
