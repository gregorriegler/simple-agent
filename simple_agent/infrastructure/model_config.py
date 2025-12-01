import os
import sys
from dataclasses import dataclass
from typing import Mapping, Any


def resolve_api_key(value: str) -> str:
    if value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        result = os.environ.get(var_name)
        if not result:
            print(f"Error: Environment variable {var_name} not set", file=sys.stderr)
            sys.exit(1)
        return result
    return value


@dataclass
class ModelConfig:
    name: str
    model: str
    adapter: str
    api_key: str
    base_url: str | None = None
    request_timeout: int = 60

    @staticmethod
    def from_dict(name: str, config: Mapping[str, Any]) -> 'ModelConfig':
        model = config.get("model") or config.get("name")
        if not model:
            print(f"Error: model.model not found in configuration '{name}'", file=sys.stderr)
            sys.exit(1)

        adapter = config.get("adapter")
        if not adapter:
            print(f"Error: model.adapter not found in configuration '{name}'", file=sys.stderr)
            sys.exit(1)

        normalized_adapter = str(adapter).strip().lower()
        if normalized_adapter not in {"claude", "openai", "gemini"}:
            print(f"Error: model.adapter must be 'claude', 'openai', or 'gemini' in configuration '{name}'", file=sys.stderr)
            sys.exit(1)

        api_key_raw = config.get("api_key")
        if not api_key_raw:
            print(f"Error: model.api_key not found in configuration '{name}'", file=sys.stderr)
            sys.exit(1)
        api_key = resolve_api_key(str(api_key_raw))

        base_url = config.get("base_url")
        if base_url is not None:
            base_url = str(base_url)

        timeout = config.get("request_timeout", 60)
        try:
            request_timeout = int(timeout)
        except (TypeError, ValueError):
            print(f"Error: model.request_timeout must be an integer in configuration '{name}'", file=sys.stderr)
            sys.exit(1)

        return ModelConfig(
            name=name,
            model=str(model),
            adapter=normalized_adapter,
            api_key=api_key,
            base_url=base_url,
            request_timeout=request_timeout
        )


class ModelsRegistry:

    def __init__(self, models: dict[str, ModelConfig], default: str):
        self.models = models
        self.default = default

    def get(self, name: str | None) -> ModelConfig:
        key = name or self.default
        if key not in self.models:
            available = ", ".join(self.models.keys())
            print(f"Error: Unknown model configuration: '{key}'. Available models: {available}", file=sys.stderr)
            sys.exit(1)
        return self.models[key]

    @staticmethod
    def from_config(config: Mapping[str, Any]) -> 'ModelsRegistry':
        model_section = config.get("model")
        if not isinstance(model_section, Mapping):
            print("Error: [model] section not found in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)

        default_name = model_section.get("default")
        if not default_name:
            print("Error: [model].default must be set to specify the default model", file=sys.stderr)
            sys.exit(1)
        default_name = str(default_name)

        models_section = config.get("models")
        if not isinstance(models_section, Mapping) or not models_section:
            print("Error: [models.*] sections are required in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)

        models_dict = {}
        for model_name, model_config in models_section.items():
            if isinstance(model_config, Mapping):
                models_dict[str(model_name)] = ModelConfig.from_dict(str(model_name), model_config)

        if default_name not in models_dict:
            available = ", ".join(models_dict.keys())
            print(f"Error: Default model '{default_name}' not found in available models: {available}", file=sys.stderr)
            sys.exit(1)

        return ModelsRegistry(models=models_dict, default=default_name)
