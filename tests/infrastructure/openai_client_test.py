import json
import pytest
import httpx

from simple_agent.infrastructure.openai.openai_client import OpenAILLM


@pytest.mark.asyncio
async def test_openai_client_sends_correct_request():
    response_data = {
        "choices": [{"message": {"content": "assistant response"}}],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json=response_data)

    transport = httpx.MockTransport(handler)

    client = OpenAILLM(StubOpenAIConfig(), transport=transport)
    messages = [{"role": "user", "content": "Hello"}]

    result = await client.call_async(messages)

    assert result.content == "assistant response"
    assert result.model == "test-openai-model"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["json"]["model"] == "test-openai-model"
    assert captured["json"]["messages"] == messages


class StubOpenAIConfig:
    def __init__(self, base_url=None):
        self._base_url = base_url

    @property
    def adapter(self):
        return "openai"

    @property
    def api_key(self):
        return "test-openai-api-key"

    @property
    def model(self):
        return "test-openai-model"

    @property
    def base_url(self):
        return self._base_url

    @property
    def request_timeout(self):
        return 60
