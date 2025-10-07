import os
import sys
import tomllib


def load_claude_config():
    home_config_path = os.path.join(os.path.expanduser("~"), ".simple-agent.toml")
    cwd_config_path = os.path.join(os.getcwd(), ".simple-agent.toml")
    
    config = {}
    if os.path.exists(home_config_path):
        config = _read_config(home_config_path)
    
    if os.path.exists(cwd_config_path):
        cwd_config = _read_config(cwd_config_path)
        config = _merge_configs(config, cwd_config)
    
    if not config:
        print(f"Error: .simple-agent.toml not found in home directory (~) or current directory ({os.getcwd()})", file=sys.stderr)
        print("Please create a .simple-agent.toml file with your Claude configuration", file=sys.stderr)
        sys.exit(1)
    
    return ClaudeConfig(config)


def default_session_file_path():
    return os.path.join(os.getcwd(), "claude-session.json")


class ClaudeConfig:
    def __init__(self, config):
        self._config = config

    @property
    def api_key(self):
        if 'claude' not in self._config or 'api_key' not in self._config['claude']:
            print("Error: claude.api_key not found in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return self._config['claude']['api_key']

    @property
    def model(self):
        if 'claude' not in self._config or 'model' not in self._config['claude']:
            print("Error: claude.model not found in .simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return self._config['claude']['model']

    @property
    def session_file_path(self):
        return default_session_file_path()


def _merge_configs(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def _script_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read_config(path):
    try:
        with open(path, 'rb') as handle:
            return tomllib.load(handle)
    except Exception as error:
        print(f"Error reading {path}: {error}", file=sys.stderr)
        sys.exit(1)