import asyncio
import io
import json
from types import SimpleNamespace

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from simple_agent.infrastructure.bedrock.bedrock_client import (
    BedrockClaudeClientError,
    BedrockClaudeLLM,
)
from simple_agent.infrastructure.model_config import ModelConfig


@pytest.mark.asyncio
async def test_bedrock_claude_chat_returns_content_text():
    response_data = {
        "content": [{"text": "assistant response"}],
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    system_prompt = "system prompt"

    client = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        aws_session_token="test",
    )
    stubber = Stubber(client)

    body_bytes = json.dumps(response_data).encode("utf-8")
    expected_body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": "Hello"}],
            "system": system_prompt,
        }
    )

    stubber.add_response(
        "invoke_model",
        {
            "body": StreamingBody(io.BytesIO(body_bytes), len(body_bytes)),
            "contentType": "application/json",
        },
        {
            "modelId": "test-model",
            "body": expected_body,
            "contentType": "application/json",
            "accept": "application/json",
        },
    )
    stubber.activate()

    chat = BedrockClaudeLLM(build_config(), client=client)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Hello"},
    ]

    result = await chat.call_async(messages)

    assert result.content == "assistant response"
    assert result.model == "test-model"
    assert result.usage is not None
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


@pytest.mark.asyncio
async def test_bedrock_claude_chat_runs_in_thread(monkeypatch):
    response_data = {
        "content": [{"text": "assistant response"}],
        "usage": {"input_tokens": 1, "output_tokens": 2},
    }
    body_bytes = json.dumps(response_data).encode("utf-8")

    class DummyClient:
        def __init__(self):
            self.meta = SimpleNamespace(endpoint_url="https://dummy-endpoint")

        def invoke_model(self, **_kwargs):
            return {
                "body": StreamingBody(io.BytesIO(body_bytes), len(body_bytes)),
                "contentType": "application/json",
            }

    called = {"to_thread": 0}

    async def fake_to_thread(func, *args, **kwargs):
        called["to_thread"] += 1
        return func(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    chat = BedrockClaudeLLM(build_config(), client=DummyClient())

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "assistant response"
    assert called["to_thread"] >= 1


@pytest.mark.asyncio
async def test_bedrock_claude_chat_raises_error_when_content_missing():
    response_data = {}

    client = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        aws_session_token="test",
    )
    stubber = Stubber(client)

    body_bytes = json.dumps(response_data).encode("utf-8")
    expected_body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": "Hello"}],
        }
    )

    stubber.add_response(
        "invoke_model",
        {
            "body": StreamingBody(io.BytesIO(body_bytes), len(body_bytes)),
            "contentType": "application/json",
        },
        {
            "modelId": "test-model",
            "body": expected_body,
            "contentType": "application/json",
            "accept": "application/json",
        },
    )
    stubber.activate()

    chat = BedrockClaudeLLM(build_config(), client=client)

    with pytest.raises(BedrockClaudeClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response missing 'content' field"


def test_bedrock_claude_client_uses_endpoint_url_from_base_url(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "test")

    config = build_config(base_url="https://bedrock-runtime.us-west-2.amazonaws.com")

    chat = BedrockClaudeLLM(config)

    assert chat._client.meta.endpoint_url == config.base_url
    assert chat._client.meta.region_name == "us-west-2"


def test_bedrock_claude_client_uses_region_from_base_url(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "test")

    config = build_config(base_url="us-west-1")

    chat = BedrockClaudeLLM(config)

    assert chat._client.meta.region_name == "us-west-1"


def build_config(base_url: str | None = None) -> ModelConfig:
    return ModelConfig(
        name="bedrock-claude",
        model="test-model",
        adapter="bedrock",
        api_key="unused",
        base_url=base_url,
        request_timeout=60,
    )
