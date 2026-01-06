import pytest
import httpx

from simple_agent.infrastructure.gemini.gemini_client import GeminiLLM


@pytest.mark.asyncio
async def test_gemini_get_input_token_limit_handles_none_base_url():
    """Test that _get_input_token_limit handles None base_url gracefully"""
    response_data = {"inputTokenLimit": 1000000}

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    config = StubGeminiConfigWithNoneBaseUrl()
    chat = GeminiLLM(config, transport=transport)

    # This should not raise AttributeError: 'NoneType' object has no attribute 'rstrip'
    limit = await chat._get_input_token_limit()

    assert limit == 1000000


class StubGeminiConfigWithNoneBaseUrl:
    def __init__(self):
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
        return None  # This triggers the bug

    @property
    def request_timeout(self):
        return 60
