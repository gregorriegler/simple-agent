import pytest
import httpx

from simple_agent.infrastructure.gemini.gemini_v1_client import GeminiV1LLM


@pytest.mark.asyncio
async def test_gemini_v1_get_input_token_limit_handles_none_base_url():
    """Test that _get_input_token_limit handles None base_url gracefully"""
    response_data = {"inputTokenLimit": 1000000}

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    config = StubGeminiV1ConfigWithNoneBaseUrl()
    chat = GeminiV1LLM(config, transport=transport)

    # This should not raise AttributeError: 'NoneType' object has no attribute 'rstrip'
    limit = await chat._get_input_token_limit()

    assert limit == 1000000


class StubGeminiV1ConfigWithNoneBaseUrl:
    def __init__(self):
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
        return None  # This triggers the bug

    @property
    def request_timeout(self):
        return 60
