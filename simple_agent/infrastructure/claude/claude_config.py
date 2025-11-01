import os
import sys

from simple_agent.infrastructure.configuration import load_user_configuration


def load_claude_config(config=None):
    config_data = config or load_user_configuration()
    return ClaudeConfig(config_data)


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
