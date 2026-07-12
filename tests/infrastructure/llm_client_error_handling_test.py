from unittest.mock import patch

import httpx
import pytest

from simple_agent.infrastructure.claude.claude_client import (
    ClaudeClientError,
    ClaudeLLM,
)
from simple_agent.infrastructure.gemini.gemini_v1_client import (
    GeminiV1ClientError,
    GeminiV1LLM,
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
        GeminiV1LLM,
        GeminiV1ClientError,
        "gemini_v1",
        {"candidates": [{"content": {"parts": [{"text": "success"}]}}]},
        id="gemini_v1",
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
