import os
import tomllib
from typing import Any, Mapping, Tuple

from simple_agent.application.agent_type import AgentType
from simple_agent.application.session import SessionArgs
from simple_agent.infrastructure.user_configuration import UserConfiguration


def load_user_configuration(cwd: str) -> UserConfiguration:
    config, found = _load_configuration_sources(cwd=cwd)

    if not found:
        raise FileNotFoundError(
            ".simple-agent.toml not found in home directory (~) or current directory "
            f"({cwd})"
        )

    return UserConfiguration(config)


def load_optional_user_configuration(cwd: str) -> UserConfiguration:
    config, _ = _load_configuration_sources(cwd=cwd)
    return UserConfiguration(config)


def stub_user_config() -> UserConfiguration:
    return UserConfiguration({})


def get_starting_agent(user_config: UserConfiguration, args: SessionArgs | None = None) -> AgentType:
    if args and args.stub_llm:
        return UserConfiguration.default_starting_agent_type()
    if args and args.agent:
        return AgentType(args.agent)
    return user_config.starting_agent_type()


def _read_config(path: str) -> Mapping[str, Any]:
    try:
        with open(path, "rb") as handle:
            return tomllib.load(handle)
    except Exception as error:  # pragma: no cover - configuration errors exit early
        raise ValueError(f"error reading {path}: {error}") from error


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

    return _resolve_api_keys(config), found


def resolve_api_key(value: str) -> str:
    if value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        result = os.environ.get(var_name)
        if not result:
            raise ValueError(f"environment variable '{var_name}' is not set")
        return result
    return value


def _resolve_api_keys(config: Mapping[str, Any]) -> Mapping[str, Any]:
    return _resolve_value(config)


def _resolve_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _resolve_api_key_value(key, child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_resolve_value(child) for child in value]
    return value


def _resolve_api_key_value(key: str, value: Any) -> Any:
    if key == "api_key" and isinstance(value, str):
        return resolve_api_key(value)
    return _resolve_value(value)


def _merge_dicts(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
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
