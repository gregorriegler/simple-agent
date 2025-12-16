import pytest
import respx
import httpx

from simple_agent.infrastructure.openai.openai_client import OpenAILLM


@respx.mock
def test_openai_client_sends_correct_request():
    response_data = {
        "choices": [{"message": {"content": "assistant response"}}],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=response_data)
    )

    client = OpenAILLM(StubOpenAIConfig())
    messages = [{"role": "user", "content": "Hello"}]

    result = client(messages)

    assert result.content == "assistant response"
    assert result.model == "test-openai-model"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


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
