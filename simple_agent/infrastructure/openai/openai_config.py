import sys

from simple_agent.infrastructure.configuration import load_user_configuration


def load_openai_config(config=None):
    config_data = config or load_user_configuration()
    return OpenAIConfig(config_data)


class OpenAIConfig:
    def __init__(self, config):
        self._config = config

    @property
    def api_key(self) -> str:
        api_key = self._config.get("openai", {}).get("api_key")
        if not api_key:
            print("Error: openai.api_key not found in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return api_key

    @property
    def model(self) -> str:
        model = self._config.get("openai", {}).get("model")
        if not model:
            print("Error: openai.model not found in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return model

    @property
    def base_url(self) -> str:
        return self._config.get("openai", {}).get("base_url", "https://api.openai.com")

    @property
    def request_timeout(self) -> int:
        return int(self._config.get("openai", {}).get("request_timeout", 60))
