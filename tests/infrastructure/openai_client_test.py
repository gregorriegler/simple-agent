import json

import httpx
import pytest

from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.infrastructure.openai.openai_client import OpenAILLM


@pytest.mark.asyncio
async def test_openai_client_sends_correct_request():
    response_data = {
        "choices": [{"message": {"content": "assistant response"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json=response_data)

    transport = httpx.MockTransport(handler)

    client = OpenAILLM(build_config(), transport=transport)
    messages = [{"role": "user", "content": "Hello"}]

    result = await client.call_async(messages)

    assert result.content == "assistant response"
    assert result.model == "test-openai-model"
    assert result.usage is not None
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["json"]["model"] == "test-openai-model"
    assert captured["json"]["messages"] == messages


def build_config(base_url: str | None = None) -> ModelConfig:
    return ModelConfig(
        name="openai",
        model="test-openai-model",
        adapter="openai",
        api_key="test-openai-api-key",
        base_url=base_url,
        request_timeout=60,
    )
