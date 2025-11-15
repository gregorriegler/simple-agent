import os
import sys
from typing import Any, Mapping


def default_session_file_path() -> str:
    return os.path.join(os.getcwd(), "claude-session.json")


class ModelConfig:
    def __init__(self, config: Mapping[str, Any]):
        self._config = config
        self._model_section = self._extract_model_section()
        self._adapter = self._extract_adapter()

    @property
    def adapter(self) -> str:
        return self._adapter

    @property
    def api_key(self) -> str:
        api_key = self._model_section.get("api_key")
        if not api_key:
            print("Error: model.api_key not found in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return str(api_key)

    @property
    def model(self) -> str:
        model_name = self._model_section.get("model") or self._model_section.get("name")
        if not model_name:
            print("Error: model.model not found in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return str(model_name)

    @property
    def base_url(self) -> str | None:
        base_url = self._model_section.get("base_url")
        if base_url is None:
            return None
        return str(base_url)

    @property
    def request_timeout(self) -> int:
        timeout = self._model_section.get("request_timeout", 60)
        try:
            return int(timeout)
        except (TypeError, ValueError):
            print("Error: model.request_timeout must be an integer", file=sys.stderr)
            sys.exit(1)

    def _extract_model_section(self) -> Mapping[str, Any]:
        model_section = self._config.get("model")
        if not isinstance(model_section, Mapping):
            print("Error: [model] section not found in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return model_section

    def _extract_adapter(self) -> str:
        adapter = self._model_section.get("adapter")
        if adapter is None:
            print("Error: model.adapter must be configured to select an adapter", file=sys.stderr)
            sys.exit(1)
        normalized = str(adapter).strip().lower()
        if normalized not in {"claude", "openai"}:
            print("Error: model.adapter must be either 'claude' or 'openai'", file=sys.stderr)
            sys.exit(1)
        return normalized
