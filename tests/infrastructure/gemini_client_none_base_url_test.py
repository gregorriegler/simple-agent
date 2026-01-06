import httpx
import pytest

from simple_agent.infrastructure.gemini.gemini_client import GeminiLLM
from simple_agent.infrastructure.model_config import ModelConfig


@pytest.mark.asyncio
async def test_gemini_get_input_token_limit_handles_none_base_url():
    """Test that _get_input_token_limit handles None base_url gracefully"""
    response_data = {"inputTokenLimit": 1000000}

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    config = ModelConfig(
        name="gemini",
        model="test-model",
        adapter="gemini",
        api_key="test-api-key",
        base_url=None,
        request_timeout=60,
    )
    chat = GeminiLLM(config, transport=transport)

    # This should not raise AttributeError: 'NoneType' object has no attribute 'rstrip'
    limit = await chat._get_input_token_limit()

    assert limit == 1000000
