from simple_agent.application.llm import LLM
from simple_agent.infrastructure.bedrock.bedrock_client import BedrockClaudeLLM
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.gemini import GeminiLLM, GeminiV1LLM
from simple_agent.infrastructure.openai import OpenAILLM
from simple_agent.infrastructure.user_configuration import UserConfiguration


class RemoteLLMProvider:
    def __init__(self, user_config: UserConfiguration):
        self._registry = user_config.models_registry()

    def get_available_models(self) -> list[str]:
        return list(self._registry.models.keys())

    def get(self, model_name: str | None = None) -> LLM:
        model_config = self._registry.get(model_name)
        if model_config.adapter == "openai":
            return OpenAILLM(model_config)

        if model_config.adapter == "gemini":
            return GeminiLLM(model_config)

        if model_config.adapter == "gemini_v1":
            return GeminiV1LLM(model_config)

        if model_config.adapter == "bedrock":
            return BedrockClaudeLLM(model_config)

        return ClaudeLLM(model_config)
