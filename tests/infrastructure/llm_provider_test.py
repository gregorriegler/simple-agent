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
                "tool_syntax": model_config.tool_syntax,
            }
        },
    }
    return UserConfiguration(config, "/tmp")


def test_remote_llm_provider_returns_openai_adapter():
    model = ModelConfig(name="openai", model="gpt-4", adapter="openai", api_key="key")
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get()

    assert isinstance(llm, OpenAILLM)


def test_remote_llm_provider_returns_gemini_adapter():
    model = ModelConfig(
        name="gemini", model="gemini-3.7-flash", adapter="gemini", api_key="key"
    )
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get()

    assert isinstance(llm, GeminiLLM)


def test_remote_llm_provider_returns_claude_adapter_by_default():
    model = ModelConfig(
        name="claude", model="claude-sonnet-4", adapter="claude", api_key="key"
    )
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get()

    assert isinstance(llm, ClaudeLLM)


def test_native_gemini_receives_the_tools():
    model = ModelConfig(
        name="gemini",
        model="gemini-3-flash",
        adapter="gemini",
        api_key="key",
        tool_syntax="native",
    )
    provider = RemoteLLMProvider(build_user_config(model))
    tools = ["tool-a", "tool-b"]

    llm = provider.get(tools=tools)

    assert isinstance(llm, GeminiLLM)
    assert llm._tools == tools


def test_emoji_gemini_ignores_the_tools():
    model = ModelConfig(
        name="gemini", model="gemini-3-flash", adapter="gemini", api_key="key"
    )
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get(tools=["tool-a"])

    assert llm._tools == []


def test_remote_llm_provider_returns_bedrock_adapter():
    model = ModelConfig(
        name="bedrock",
        model="claude-3-haiku-20240307-v1:0",
        adapter="bedrock",
        api_key="unused",
    )
    provider = RemoteLLMProvider(build_user_config(model))

    llm = provider.get()

    assert isinstance(llm, BedrockClaudeLLM)
