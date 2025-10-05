import os
import sys
import tomllib


def load_claude_config():
    script_dir = _script_dir()
    config_path = os.path.join(os.getcwd(), "simple-agent.toml")
    config = _read_config(config_path)
    return ClaudeConfig(config, script_dir)


def default_session_file_path():
    return os.path.join(os.getcwd(), "claude-session.json")


class ClaudeConfig:
    def __init__(self, config, script_dir):
        self._config = config
        self._script_dir = script_dir

    @property
    def api_key(self):
        if 'claude' not in self._config or 'api_key' not in self._config['claude']:
            print("Error: claude.api_key not found in simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return self._config['claude']['api_key']

    @property
    def model(self):
        if 'claude' not in self._config or 'model' not in self._config['claude']:
            print("Error: claude.model not found in simple-agent.toml", file=sys.stderr)
            sys.exit(1)
        return self._config['claude']['model']

    @property
    def session_file_path(self):
        return default_session_file_path()


def _script_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read_config(path):
    if not os.path.exists(path):
        print(f"Error: simple-agent.toml not found in current directory ({os.getcwd()})", file=sys.stderr)
        print("Please create a simple-agent.toml file with your Claude configuration", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, 'rb') as handle:
            return tomllib.load(handle)
    except Exception as error:
        print(f"Error reading {path}: {error}", file=sys.stderr)
        sys.exit(1)
