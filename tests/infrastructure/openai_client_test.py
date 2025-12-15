import pytest

from simple_agent.infrastructure.openai.openai_client import OpenAILLM


def test_openai_client_sends_correct_request(httpserver):
    response_data = {
        "choices": [{"message": {"content": "assistant response"}}],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

    httpserver.expect_request(
        "/chat/completions",
        method="POST",
        json={
            "model": "test-openai-model",
            "messages": [{"role": "user", "content": "Hello"}]
        },
        headers={"Authorization": "Bearer test-openai-api-key"}
    ).respond_with_json(response_data)

    client = OpenAILLM(StubOpenAIConfig(base_url=httpserver.url_for("")))
    messages = [{"role": "user", "content": "Hello"}]

    result = client(messages)

    assert result.content == "assistant response"
    assert result.model == "test-openai-model"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


class StubOpenAIConfig:
    def __init__(self, base_url):
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
