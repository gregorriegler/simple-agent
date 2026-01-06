from dataclasses import dataclass
from typing import Mapping, Any


@dataclass
class ModelConfig:
    name: str
    model: str
    adapter: str
    api_key: str
    base_url: str | None = None
    request_timeout: int = 60

    @staticmethod
    def from_dict(name: str, config: Mapping[str, Any]) -> "ModelConfig":
        model = config.get("model") or config.get("name")
        if not model:
            raise ValueError(f"model '{name}' is missing required field 'model'")

        adapter = config.get("adapter")
        if not adapter:
            raise ValueError(f"model '{name}' is missing required field 'adapter'")

        normalized_adapter = str(adapter).strip().lower()

        api_key_raw = config.get("api_key")
        if not api_key_raw:
            raise ValueError(f"model '{name}' is missing required field 'api_key'")
        api_key = str(api_key_raw)

        base_url = config.get("base_url")
        if base_url is not None:
            base_url = str(base_url)

        timeout = config.get("request_timeout", 60)
        try:
            request_timeout = int(timeout)
        except (TypeError, ValueError):
            raise ValueError(
                f"model '{name}' has non-integer 'request_timeout': {timeout!r}"
            )

        return ModelConfig(
            name=name,
            model=str(model),
            adapter=normalized_adapter,
            api_key=api_key,
            base_url=base_url,
            request_timeout=request_timeout,
        )


class ModelsRegistry:
    def __init__(self, models: dict[str, ModelConfig], default: str):
        self.models = models
        self.default = default

    def get(self, name: str | None) -> ModelConfig:
        key = name or self.default
        if key not in self.models:
            return self.models[self.default]
        return self.models[key]

    @staticmethod
    def from_config(config: Mapping[str, Any]) -> "ModelsRegistry":
        model_section = config.get("model")
        if not isinstance(model_section, Mapping):
            raise ValueError("missing required 'model' section in configuration")

        default_name = model_section.get("default")
        if not default_name:
            raise ValueError("missing required 'model.default' value in configuration")
        default_name = str(default_name)

        models_section = config.get("models")
        if not isinstance(models_section, Mapping) or not models_section:
            raise ValueError("missing required 'models' section in configuration")

        models_dict = {}
        for model_name, model_config in models_section.items():
            if isinstance(model_config, Mapping):
                models_dict[str(model_name)] = ModelConfig.from_dict(
                    str(model_name), model_config
                )

        if default_name not in models_dict:
            available = ", ".join(models_dict.keys())
            raise ValueError(
                f"default model '{default_name}' not found in available models: {available}"
            )

        return ModelsRegistry(models=models_dict, default=default_name)
