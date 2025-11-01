import os
import sys
import tomllib
from typing import Any, Mapping


def load_user_configuration() -> Mapping[str, Any]:
    home_config_path = os.path.join(os.path.expanduser("~"), ".simple-agent.toml")
    cwd_config_path = os.path.join(os.getcwd(), ".simple-agent.toml")

    config: dict[str, Any] = {}
    found = False

    if os.path.exists(home_config_path):
        config = _read_config(home_config_path)
        found = True

    if os.path.exists(cwd_config_path):
        cwd_config = _read_config(cwd_config_path)
        config = _merge_dicts(config, cwd_config)
        found = True

    if not found:
        print(
            "Error: .simple-agent.toml not found in home directory (~) or current directory"
            f" ({os.getcwd()})",
            file=sys.stderr,
        )
        print(
            "Please create a .simple-agent.toml file with your LLM configuration",
            file=sys.stderr,
        )
        sys.exit(1)

    return config


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


def _read_config(path: str) -> Mapping[str, Any]:
    try:
        with open(path, "rb") as handle:
            return tomllib.load(handle)
    except Exception as error:  # pragma: no cover - configuration errors exit early
        print(f"Error reading {path}: {error}", file=sys.stderr)
        sys.exit(1)
