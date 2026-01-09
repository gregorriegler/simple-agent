import json
import pytest
from unittest.mock import MagicMock, patch
from simple_agent.infrastructure.bedrock.bedrock_client import BedrockClaudeLLM
from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.application.llm import TokenUsage

@pytest.fixture
def mock_boto3_client():
    with patch("boto3.client") as mock_client:
        yield mock_client

def test_ensure_bedrock_adapter():
    config = ModelConfig(name="test", model="claude-3-haiku", adapter="openai", api_key="dummy")
    with pytest.raises(RuntimeError, match="Configured adapter is not 'bedrock'"):
        BedrockClaudeLLM(config)

def test_bedrock_client_initialization(mock_boto3_client):
    config = ModelConfig(name="test", model="claude-3-haiku", adapter="bedrock", api_key="us-east-1")
    llm = BedrockClaudeLLM(config)
    mock_boto3_client.assert_called_with("bedrock-runtime", region_name="us-east-1")
    assert llm.model == "claude-3-haiku"

@pytest.mark.asyncio
async def test_call_async(mock_boto3_client):
    config = ModelConfig(name="test", model="anthropic.claude-3-haiku-20240307-v1:0", adapter="bedrock", api_key="us-west-2")
    llm = BedrockClaudeLLM(config)

    mock_invoke = MagicMock()
    mock_boto3_client.return_value.invoke_model = mock_invoke

    # Mock response
    response_body = {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello, world!"}],
        "usage": {"input_tokens": 10, "output_tokens": 5}
    }
    mock_response_stream = MagicMock()
    mock_response_stream.read.return_value = json.dumps(response_body).encode("utf-8")

    mock_invoke.return_value = {"body": mock_response_stream}

    messages = [{"role": "user", "content": "Hi"}]
    response = await llm.call_async(messages)

    assert response.content == "Hello, world!"
    assert response.model == "anthropic.claude-3-haiku-20240307-v1:0"
    assert response.usage == TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15)

    # Verify call arguments
    args, kwargs = mock_invoke.call_args
    assert kwargs["modelId"] == "anthropic.claude-3-haiku-20240307-v1:0"
    body = json.loads(kwargs["body"])
    assert body["anthropic_version"] == "bedrock-2023-05-31"
    assert body["max_tokens"] == 4000
    assert body["messages"] == [{"role": "user", "content": "Hi"}]

@pytest.mark.asyncio
async def test_call_async_with_system_prompt(mock_boto3_client):
    config = ModelConfig(name="test", model="claude-3", adapter="bedrock", api_key="dummy")
    llm = BedrockClaudeLLM(config)

    mock_invoke = MagicMock()
    mock_boto3_client.return_value.invoke_model = mock_invoke

    mock_response_stream = MagicMock()
    mock_response_stream.read.return_value = json.dumps({
        "content": [{"type": "text", "text": "Response"}],
        "usage": {}
    }).encode("utf-8")
    mock_invoke.return_value = {"body": mock_response_stream}

    messages = [
        {"role": "system", "content": "System instruction"},
        {"role": "user", "content": "User query"}
    ]
    await llm.call_async(messages)

    args, kwargs = mock_invoke.call_args
    body = json.loads(kwargs["body"])
    assert body["system"] == "System instruction"
    assert len(body["messages"]) == 1
    assert body["messages"][0] == [{"role": "user", "content": "User query"}][0]
