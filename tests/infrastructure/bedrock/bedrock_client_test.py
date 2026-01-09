import json
import pytest
from unittest.mock import MagicMock, patch
from simple_agent.infrastructure.bedrock.bedrock_client import BedrockClaudeLLM, BedrockClientError
from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.application.llm import ChatMessages

@pytest.fixture
def mock_boto3_client():
    with patch("boto3.client") as mock:
        yield mock

@pytest.fixture
def model_config():
    return ModelConfig(
        name="bedrock-claude",
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        adapter="bedrock",
        api_key="us-east-1"
    )

@pytest.mark.asyncio
async def test_bedrock_claude_llm_call_async(mock_boto3_client, model_config):
    # Setup mock
    mock_client_instance = MagicMock()
    mock_boto3_client.return_value = mock_client_instance

    mock_response_body = {
        "content": [{"text": "Hello, world!"}],
        "usage": {"input_tokens": 10, "output_tokens": 5}
    }

    # Mock the response from invoke_model
    # The response body is a streaming body, so we mock .read()
    mock_body_stream = MagicMock()
    mock_body_stream.read.return_value = json.dumps(mock_response_body).encode("utf-8")

    mock_client_instance.invoke_model.return_value = {
        "body": mock_body_stream
    }

    # Initialize LLM
    llm = BedrockClaudeLLM(model_config)

    # Define messages
    messages: ChatMessages = [{"role": "user", "content": "Hi"}]

    # Call async method
    response = await llm.call_async(messages)

    # Assertions
    assert response.content == "Hello, world!"
    assert response.model == "anthropic.claude-3-sonnet-20240229-v1:0"
    assert response.usage.input_tokens == 10
    assert response.usage.output_tokens == 5

    # Verify boto3 call
    mock_client_instance.invoke_model.assert_called_once()
    call_kwargs = mock_client_instance.invoke_model.call_args[1]
    assert call_kwargs["modelId"] == "anthropic.claude-3-sonnet-20240229-v1:0"

    request_body = json.loads(call_kwargs["body"])
    assert request_body["anthropic_version"] == "bedrock-2023-05-31"
    assert request_body["messages"] == [{"role": "user", "content": "Hi"}]

@pytest.mark.asyncio
async def test_bedrock_claude_llm_with_system_prompt(mock_boto3_client, model_config):
    # Setup mock
    mock_client_instance = MagicMock()
    mock_boto3_client.return_value = mock_client_instance

    mock_response_body = {
        "content": [{"text": "Response"}],
        "usage": {}
    }
    mock_body_stream = MagicMock()
    mock_body_stream.read.return_value = json.dumps(mock_response_body).encode("utf-8")
    mock_client_instance.invoke_model.return_value = {"body": mock_body_stream}

    llm = BedrockClaudeLLM(model_config)

    messages: ChatMessages = [
        {"role": "system", "content": "Be helpful"},
        {"role": "user", "content": "Hi"}
    ]

    await llm.call_async(messages)

    call_kwargs = mock_client_instance.invoke_model.call_args[1]
    request_body = json.loads(call_kwargs["body"])

    assert request_body["system"] == "Be helpful"
    assert request_body["messages"] == [{"role": "user", "content": "Hi"}]

def test_bedrock_adapter_validation():
    config = ModelConfig(name="test", model="test", adapter="claude", api_key="key")
    with pytest.raises(BedrockClientError, match="Configured adapter is not 'bedrock'"):
        BedrockClaudeLLM(config)
