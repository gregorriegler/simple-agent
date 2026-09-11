import asyncio
import io
import json
import logging
from types import SimpleNamespace

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from simple_agent.application.llm import (
    AssistantMessage,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.tool_library import (
    ToolArgument,
    ToolArguments,
    ToolCall,
)
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
        SystemMessage(system_prompt),
        UserMessage("Hello"),
    ]

    result = await chat.call_async(messages)

    assert result.answer == "assistant response"
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

    result = await chat.call_async([UserMessage("Hello")])

    assert result.answer == "assistant response"
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
        await chat.call_async([UserMessage("Hello")])

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


@pytest.mark.asyncio
async def test_bedrock_claude_logs_requests_and_responses(caplog):
    caplog.set_level(logging.DEBUG)

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
            # removed statusCode
        },
        {
            "modelId": "test-model",
            "body": expected_body,
            "contentType": "application/json",
            "accept": "application/json",
        },
    )
    stubber.activate()

    config = ModelConfig(
        name="bedrock-claude",
        model="test-model",
        adapter="bedrock",
        api_key="unused",
        base_url=None,
        request_timeout=60,
    )
    chat = BedrockClaudeLLM(config, client=client)
    messages = [
        SystemMessage(system_prompt),
        UserMessage("Hello"),
    ]

    await chat.call_async(messages)

    # Filter for our logger to avoid botocore noise if any
    logs = [
        r.message
        for r in caplog.records
        if r.name == "simple_agent.infrastructure.bedrock.bedrock_client"
    ]
    full_log = "\n".join(logs)

    expected_request_part = """POST https://bedrock-runtime.us-east-1.amazonaws.com/model/test-model/invoke HTTP/1.1
Content-Type: application/json
Accept: application/json

{
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 4000,
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "system": "system prompt"
}"""

    # We expect compact JSON because Content-Type header is missing in the stubbed response metadata
    expected_response_part = """HTTP/1.1 200 OK

{"content": [{"text": "assistant response"}], "usage": {"input_tokens": 10, "output_tokens": 20}}"""

    assert expected_request_part in full_log
    assert expected_response_part in full_log


def build_config(base_url: str | None = None) -> ModelConfig:
    return ModelConfig(
        name="bedrock-claude",
        model="test-model",
        adapter="bedrock",
        api_key="unused",
        base_url=base_url,
        request_timeout=60,
    )


def build_tool(name: str) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        description=f"{name} tool",
        arguments=ToolArguments(
            header=[ToolArgument(name="filename", description="", required=True)]
        ),
    )


class RecordingClient:
    def __init__(self, response_data: dict):
        self.meta = SimpleNamespace(endpoint_url="https://dummy-endpoint")
        self.requests: list[dict] = []
        self._body = json.dumps(response_data).encode("utf-8")

    def invoke_model(self, **kwargs):
        self.requests.append(json.loads(kwargs["body"]))
        return {
            "body": StreamingBody(io.BytesIO(self._body), len(self._body)),
            "contentType": "application/json",
        }


@pytest.mark.asyncio
async def test_bedrock_claude_chat_declares_its_tools():
    client = RecordingClient({"content": [{"type": "text", "text": "ok"}]})
    chat = BedrockClaudeLLM(build_config(), tools=[build_tool("cat")], client=client)

    await chat.call_async([UserMessage("Hello")])

    assert [tool["name"] for tool in client.requests[0]["tools"]] == ["cat"]
    assert client.requests[0]["tools"][0]["input_schema"]["required"] == ["filename"]


@pytest.mark.asyncio
async def test_bedrock_claude_chat_without_tools_declares_none():
    client = RecordingClient({"content": [{"type": "text", "text": "ok"}]})
    chat = BedrockClaudeLLM(build_config(), client=client)

    await chat.call_async([UserMessage("Hello")])

    assert "tools" not in client.requests[0]


@pytest.mark.asyncio
async def test_bedrock_claude_chat_reads_tool_use_blocks_into_bound_calls():
    client = RecordingClient(
        {
            "content": [
                {"type": "text", "text": "Let me look."},
                {
                    "type": "tool_use",
                    "id": "toolu_abc",
                    "name": "cat",
                    "input": {"filename": "notes.md"},
                },
            ],
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
    )
    chat = BedrockClaudeLLM(build_config(), tools=[build_tool("cat")], client=client)

    result = await chat.call_async([UserMessage("show notes")])

    assert result.answer == "Let me look."
    assert result.tool_calls == [
        ToolCall(
            "cat", {"filename": "notes.md"}, provider_state={"native_id": "toolu_abc"}
        )
    ]


@pytest.mark.asyncio
async def test_bedrock_claude_chat_replays_tool_turns_as_blocks():
    client = RecordingClient({"content": [{"type": "text", "text": "ok"}]})
    chat = BedrockClaudeLLM(build_config(), tools=[build_tool("cat")], client=client)
    call = ToolCall(
        "cat", {"filename": "notes.md"}, provider_state={"native_id": "toolu_abc"}
    )

    await chat.call_async(
        [
            UserMessage("show notes"),
            AssistantMessage("Let me look.", tool_calls=[call]),
            ToolResultMessage(call, "the notes"),
        ]
    )

    assert client.requests[0]["messages"] == [
        {"role": "user", "content": "show notes"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Let me look."},
                {
                    "type": "tool_use",
                    "id": "toolu_abc",
                    "name": "cat",
                    "input": {"filename": "notes.md"},
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_abc",
                    "content": "the notes",
                }
            ],
        },
    ]
