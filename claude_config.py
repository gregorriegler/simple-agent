import os
import sys

class ClaudeConfig:
    def __init__(self):
        self._script_dir = os.path.dirname(os.path.abspath(__file__))

    def _get_absolute_path(self, filename):
        return os.path.join(self._script_dir, filename)

    def _read_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Error: {filename} not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading {filename}: {e}", file=sys.stderr)
            sys.exit(1)

    @property
    def api_key(self):
        return self._read_file(self._get_absolute_path("claude-api-key.txt"))

    @property
    def model(self):
        return self._read_file(self._get_absolute_path("claude-model.txt"))

    @property
    def session_file_path(self):
        return self._get_absolute_path("claude-session.json")

claude_config = ClaudeConfig()
