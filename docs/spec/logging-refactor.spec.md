# Logging Refactor

## Problem

The current logging system has several issues:

1. **Logs in working directory** - Both `.simple-agent.events.log` and `request.log` are created in the current working directory. This is problematic because the agent could read/write to these files, potentially creating infinite loops.

2. **Redundant logs** - There are two separate logs (event log and request log), but due to Python's `logging.basicConfig` being called in the LLM clients, all logs bleed into `request.log`, making it contain events too.

3. **Misleading naming** - `request.log` contains more than just requests.

4. **Non-standard logging setup** - `logging.basicConfig` is called at module import time in multiple places (`claude_client.py`, `openai_client.py`), which is not idiomatic Python and causes the log bleed issue.

### Relevant files:
- [simple_agent/infrastructure/event_logger.py](../../simple_agent/infrastructure/event_logger.py) - EventLogger class
- [simple_agent/infrastructure/claude/claude_client.py](../../simple_agent/infrastructure/claude/claude_client.py) - Claude client with basicConfig
- [simple_agent/infrastructure/openai/openai_client.py](../../simple_agent/infrastructure/openai/openai_client.py) - OpenAI client with basicConfig
- [simple_agent/main.py](../../simple_agent/main.py) - Where EventLogger is instantiated

## Solution

1. **Move logs to user directory**: `~/.simple-agent/logs/simple-agent.log`

2. **Merge into single log file**: One unified log for both events and LLM requests/responses.

3. **Centralize logging configuration**: 
   - Remove `logging.basicConfig` calls from LLM clients
   - Configure logging once in `main.py` (or a dedicated logging setup module)
   - Use a named logger hierarchy (e.g., `simple_agent.*`) so all app logs go to the same file

4. **Create log directory if needed**: Ensure `~/.simple-agent/logs/` exists before writing.

5. **Log format**: Keep timestamp + message, include logger name to distinguish sources:
   ```
   2024-01-15 10:30:45 - simple_agent.claude - Request: {...}
   2024-01-15 10:30:46 - simple_agent.events - AssistantSaidEvent: {...}
   ```