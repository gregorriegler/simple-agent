from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.gemini import GeminiLLM, GeminiV1LLM
from simple_agent.infrastructure.llm import RemoteLLMProvider
from simple_agent.infrastructure.model_config import ModelConfig, ModelsRegistry
from simple_agent.infrastructure.openai import OpenAILLM


class UserConfigStub:
    def __init__(self, model_config: ModelConfig):
        self._registry = ModelsRegistry(
            models={model_config.name: model_config}, default=model_config.name
        )

    def models_registry(self) -> ModelsRegistry:
        return self._registry


def test_remote_llm_provider_returns_openai_adapter():
    model = ModelConfig(name="openai", model="gpt-4", adapter="openai", api_key="key")
    provider = RemoteLLMProvider(UserConfigStub(model))

    llm = provider.get()

    assert isinstance(llm, OpenAILLM)


def test_remote_llm_provider_returns_gemini_adapter():
    model = ModelConfig(
        name="gemini", model="gemini-pro", adapter="gemini", api_key="key"
    )
    provider = RemoteLLMProvider(UserConfigStub(model))

    llm = provider.get()

    assert isinstance(llm, GeminiLLM)


def test_remote_llm_provider_returns_gemini_v1_adapter():
    model = ModelConfig(
        name="gemini-v1", model="gemini-pro", adapter="gemini_v1", api_key="key"
    )
    provider = RemoteLLMProvider(UserConfigStub(model))

    llm = provider.get()

    assert isinstance(llm, GeminiV1LLM)


def test_remote_llm_provider_returns_claude_adapter_by_default():
    model = ModelConfig(
        name="claude", model="claude-sonnet-4", adapter="claude", api_key="key"
    )
    provider = RemoteLLMProvider(UserConfigStub(model))

    llm = provider.get()

    assert isinstance(llm, ClaudeLLM)
