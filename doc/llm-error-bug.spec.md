# LLM Error Handling Bug Specification

## Problem Description

When the LLM API responds with an error (e.g., HTTP 429 rate limit), the UI appears frozen. The user sees no feedback indicating that an error occurred.

## Root Cause Analysis

### Exception Flow

1. User sends a prompt
2. `Agent.llm_responds()` calls `self.llm(self.context.to_list())` at `agent.py:95`
3. `ClaudeLLM.__call__()` raises `ClaudeClientError` on HTTP errors (e.g., 429)
4. Exception propagates up - **no event is emitted to the UI**
5. UI remains in "waiting for response" state indefinitely

### Missing Components

| Component | File | Issue |
|-----------|------|-------|
| `ErrorEvent` | `events.py` | Does not exist |
| Error catch | `agent.py:64-84` | `run_tool_loop()` only catches `KeyboardInterrupt` |
| Error handler | `display_hub.py` | No `error_occurred()` method |

### Code References

**agent.py:94-98** - No error handling around LLM call:
```python
def llm_responds(self) -> MessageAndParsedTools:
    answer = self.llm(self.context.to_list())  # exception raised here
    self.context.assistant_says(answer)
    self.event_bus.publish(AssistantRespondedEvent(self.agent_id, answer))
    return self.tools.parse_message_and_tools(answer)
```

**agent.py:64-84** - Only catches `KeyboardInterrupt`:
```python
def run_tool_loop(self):
    # ...
    except KeyboardInterrupt:
        self.event_bus.publish(SessionInterruptedEvent(self.agent_id))
        raise
```

## Proposed Solution

1. Add `ErrorEvent` to `events.py`
2. Catch exceptions in `run_tool_loop()`, emit `ErrorEvent`
3. Add `error_occurred(event)` handler in `display_hub.py`
4. Update Textual UI to display error messages
