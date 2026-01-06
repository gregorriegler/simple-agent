import os
import tomllib
from pathlib import Path


class ConfigurationError(Exception):
    pass


from typing import Mapping, Any, Self, Tuple

from simple_agent.application.agent_type import AgentType
from simple_agent.application.session import SessionArgs
from simple_agent.infrastructure.model_config import ModelsRegistry

DEFAULT_STARTING_AGENT_TYPE = "orchestrator"
APP_DIR = str(Path(__file__).resolve().parents[2])


class UserConfiguration:
    @classmethod
    def create_from_args(cls, args: SessionArgs, cwd: str) -> Self:
        if args.stub_llm:
            return cls.create_stub()
        return cls.load_from_config_file(cwd)

    @classmethod
    def create_stub(cls) -> Self:
        return cls({}, "/tmp")

    @classmethod
    def load_from_config_file(cls, cwd: str) -> Self:
        config, found = _load_configuration_sources(cwd=cwd)

        if not found:
            raise FileNotFoundError(
                ".simple-agent.toml not found in home directory (~) or current directory "
                f"({cwd})"
            )

        return cls(config, cwd)

    def __init__(self, config: Mapping[str, Any], cwd: str = "/tmp"):
        self._config = config
        self._cwd = cwd

    def agents_path(self) -> str | None:
        agents_section = self._config.get("agents")
        if isinstance(agents_section, Mapping):
            value = agents_section.get("path")
            if value:
                return str(value)
        return None

    def agents_candidate_directories(self) -> list[str]:
        agents_path = self.agents_path()
        if not agents_path:
            return [os.path.join(self._cwd, ".simple-agent", "agents")]

        result = os.path.expanduser(agents_path)
        if not os.path.isabs(result):
            result = os.path.abspath(os.path.join(self._cwd, result))
        return [result]

    def starting_agent_type(self) -> AgentType:
        agents_section = self._config.get("agents")
        if isinstance(agents_section, Mapping):
            value = agents_section.get("start")
            if value is not None:
                normalized = str(value).strip()
                if normalized:
                    return AgentType(normalized)
        return self.default_starting_agent_type()

    @staticmethod
    def default_starting_agent_type():
        return AgentType(DEFAULT_STARTING_AGENT_TYPE)

    def models_registry(self) -> ModelsRegistry:
        return ModelsRegistry.from_config(self._config)

    def log_level(self) -> str:
        log_section = self._config.get("log")
        if isinstance(log_section, Mapping):
            value = log_section.get("level")
            if value:
                return str(value).upper()
        return "INFO"

    def logger_levels(self) -> dict[str, str]:
        log_section = self._config.get("log")
        if isinstance(log_section, Mapping):
            loggers = log_section.get("loggers")
            if isinstance(loggers, Mapping):
                return {logger: str(level).upper() for logger, level in loggers.items()}
        return {}


def _read_config(path: str) -> Mapping[str, Any]:
    try:
        with open(path, "rb") as handle:
            return tomllib.load(handle)
    except Exception as error:  # pragma: no cover - configuration errors exit early
        raise ConfigurationError(f"error reading {path}: {error}") from error


def _load_configuration_sources(cwd: str) -> Tuple[Mapping[str, Any], bool]:
    home_config_path = os.path.join(os.path.expanduser("~"), ".simple-agent.toml")
    cwd_config_path = os.path.join(cwd, ".simple-agent.toml")

    config: Mapping[str, Any] = {}
    found = False

    if os.path.exists(home_config_path):
        config = _read_config(home_config_path)
        found = True

    if os.path.exists(cwd_config_path):
        cwd_config = _read_config(cwd_config_path)
        config = _merge_dicts(config, cwd_config)
        found = True

    return _resolve_value(config), found


def _resolve_api_key(value: str) -> str:
    if value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        result = os.environ.get(var_name)
        if not result:
            raise ConfigurationError(f"environment variable '{var_name}' is not set")
        return result
    return value


def _resolve_app_dir(value: str) -> str:
    if "${APP_DIR}" not in value:
        return value
    return value.replace("${APP_DIR}", APP_DIR)


def _resolve_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _resolve_api_key_value(key, child) for key, child in value.items()}
    if isinstance(value, list):
        return [_resolve_value(child) for child in value]
    if isinstance(value, str):
        return _resolve_app_dir(value)
    return value


def _resolve_api_key_value(key: str, value: Any) -> Any:
    if isinstance(value, str):
        resolved = _resolve_app_dir(value)
        if key == "api_key":
            return _resolve_api_key(resolved)
        return resolved
    return _resolve_value(value)


def _merge_dicts(
    base: Mapping[str, Any], override: Mapping[str, Any]
) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], Mapping)
            and isinstance(value, Mapping)
        ):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
