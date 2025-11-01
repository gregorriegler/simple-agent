from simple_agent.infrastructure.openai import openai_client
from simple_agent.infrastructure.openai.openai_client import OpenAILLM


def test_openai_client_respects_base_url_override(monkeypatch):
    captured = {}
    monkeypatch.setattr(openai_client.requests, "post", _create_successful_post(captured))
    client = OpenAILLM(StubOpenAIConfig(base_url="https://openrouter.ai/api/v1"))
    messages = [
        {"role": "user", "content": "Hello"}
    ]

    result = client(messages)

    assert result == "assistant response"
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["timeout"] == 60


def _create_successful_post(captured):
    response = _ResponseStub({"choices": [{"message": {"content": "assistant response"}}]})

    def post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return response

    return post


class _ResponseStub:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


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
