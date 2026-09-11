from types import SimpleNamespace

from simple_agent.infrastructure.bedrock.bedrock_client import BedrockClaudeLLM
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.gemini import GeminiLLM
from simple_agent.infrastructure.llm import RemoteLLMProvider
from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.infrastructure.openai import OpenAILLM
from simple_agent.infrastructure.user_configuration import UserConfiguration


def build_user_config(model_config: ModelConfig) -> UserConfiguration:
    config = {
        "model": {"default": model_config.name},
        "models": {
            model_config.name: {
                "model": model_config.model,
                "adapter": model_config.adapter,
                "api_key": model_config.api_key,
                "base_url": model_config.base_url,
                "request_timeout": model_config.request_timeout,
            }
        },
    }
    return UserConfiguration(config, "/tmp")


TOOLS = [SimpleNamespace(name="tool-a"), SimpleNamespace(name="tool-b")]


def test_openai_is_native_and_receives_the_tools():
    model = ModelConfig(name="openai", model="gpt-4", adapter="openai", api_key="key")
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get(tools=TOOLS)

    assert isinstance(llm, OpenAILLM)
    assert llm._tools == TOOLS


def test_gemini_is_native_and_receives_the_tools():
    model = ModelConfig(
        name="gemini", model="gemini-3.7-flash", adapter="gemini", api_key="key"
    )
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get(tools=TOOLS)

    assert isinstance(llm, GeminiLLM)
    assert llm._tools == TOOLS


def test_claude_is_native_and_receives_the_tools():
    model = ModelConfig(
        name="claude", model="claude-sonnet-4", adapter="claude", api_key="key"
    )
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get(tools=TOOLS)

    assert isinstance(llm, ClaudeLLM)
    assert llm._tools == TOOLS


def test_provider_reports_native_tool_syntax():
    model = ModelConfig(
        name="gemini", model="gemini-3-flash", adapter="gemini", api_key="key"
    )
    provider = RemoteLLMProvider(build_user_config(model))

    assert provider.tool_syntax() == "native"


def test_bedrock_is_native_and_receives_the_tools(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    model = ModelConfig(
        name="bedrock",
        model="claude-3-haiku-20240307-v1:0",
        adapter="bedrock",
        api_key="unused",
    )
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get(tools=TOOLS)

    assert isinstance(llm, BedrockClaudeLLM)
    assert llm._tools == TOOLS
