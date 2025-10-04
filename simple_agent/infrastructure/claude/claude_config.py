import os
import sys
import tomllib

class ClaudeConfig:
    def __init__(self):
        self._script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._config = self._load_config()

    def _load_config(self):
        cwd_config_path = os.path.join(os.getcwd(), "simple-agent.toml")
        if not os.path.exists(cwd_config_path):
            print(f"Error: simple-agent.toml not found in current directory ({os.getcwd()})", file=sys.stderr)
            print("Please create a simple-agent.toml file with your Claude configuration", file=sys.stderr)
            sys.exit(1)

        try:
            with open(cwd_config_path, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            print(f"Error reading {cwd_config_path}: {e}", file=sys.stderr)
            sys.exit(1)

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
        return os.path.join(self._script_dir, "claude-session.json")

claude_config = ClaudeConfig()
