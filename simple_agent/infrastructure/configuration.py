import os
import sys
import tomllib
from typing import Any, Mapping, Tuple

from simple_agent.application.session import SessionArgs

DEFAULT_STARTING_AGENT_TYPE = "orchestrator"


def load_user_configuration(cwd: str) -> Mapping[str, Any]:
    config, found = _load_configuration_sources(cwd=cwd)

    if not found:
        print(
            "Error: .simple-agent.toml not found in home directory (~) or current directory"
            f" ({cwd})",
            file=sys.stderr,
        )
        print(
            "Please create a .simple-agent.toml file with your LLM configuration",
            file=sys.stderr,
        )
        sys.exit(1)

    return config


def load_optional_user_configuration(cwd: str) -> Mapping[str, Any]:
    config, _ = _load_configuration_sources(cwd=cwd)
    return config


def get_starting_agent_type(config: Mapping[str, Any], args: SessionArgs | None = None) -> str:
    if args and args.agent:
        return args.agent
    return _extract_starting_agent_type(config) or DEFAULT_STARTING_AGENT_TYPE


def _read_config(path: str) -> Mapping[str, Any]:
    try:
        with open(path, "rb") as handle:
            return tomllib.load(handle)
    except Exception as error:  # pragma: no cover - configuration errors exit early
        print(f"Error reading {path}: {error}", file=sys.stderr)
        sys.exit(1)


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

    return config, found


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


def _extract_starting_agent_type(config: Mapping[str, Any]) -> str | None:
    agents_section = config.get("agents")
    if isinstance(agents_section, Mapping):
        for key in ("starting_agent", "start"):
            value = agents_section.get(key)
            if value is None:
                continue
            normalized = str(value).strip()
            if normalized:
                return normalized
    return None
