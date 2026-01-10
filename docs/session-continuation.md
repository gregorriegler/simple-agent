# Session Continuation

This document describes how session continuation works when using `./agent.sh -c` to resume a previous session.

## Overview

When continuing a session, the application:
1. Loads the most recent session from `.simple-agent/sessions/`
2. Replays stored messages as events to rebuild the UI state
3. Restores token usage metadata for the tab titles

## File Structure

Sessions are stored in the following structure:

```
.simple-agent/sessions/{session-id}/
├── manifest.json           # Session metadata (id, created_at, cwd)
└── agents/
    ├── Agent/
    │   ├── messages.json   # Conversation history
    │   └── metadata.json   # Token usage (model, max_tokens, input_tokens)
    └── Agent-Coding/
        ├── messages.json
        └── metadata.json
```

## Implementation

### Key Components

1. **Session Storage** (`simple_agent/application/session_storage.py`)
   - `AgentMetadata` dataclass: stores `model`, `max_tokens`, `input_tokens`
   - Protocol methods: `load_metadata()`, `save_metadata()`, `list_stored_agents()`

2. **File Session Storage** (`simple_agent/infrastructure/file_session_storage.py`)
   - `list_stored_agents()`: scans `agents/` directory to discover all stored agents
   - `load_metadata()` / `save_metadata()`: persist token usage in `metadata.json`

3. **History Replayer** (`simple_agent/application/history_replayer.py`)
   - Converts stored messages into UI events
   - `UserPromptedEvent` for user messages
   - `AssistantSaidEvent` for assistant messages
   - `AgentStartedEvent` for subagent tabs
   - `AssistantRespondedEvent` for token usage restoration

4. **Session** (`simple_agent/application/session.py`)
   - Subscribes to `AssistantRespondedEvent` to save metadata on each LLM response
   - Calls `HistoryReplayer.replay_all_agents()` when `continue_session=True`

### Event Flow on Continuation

```
Session.run_async()
  └── HistoryReplayer.replay_all_agents()
      ├── For each stored agent (sorted by depth):
      │   ├── Load metadata
      │   ├── AgentStartedEvent (for subagents only)
      │   └── For each message:
      │       ├── UserPromptedEvent
      │       └── AssistantSaidEvent
      │   └── AssistantRespondedEvent (with token metadata)
```

## Subagent Restoration via Message Stream Parsing

Subagent restoration happens **via parsing tool calls in the message stream**, not by scanning the filesystem. This ensures:

- Correct focus/tab switching order matching the original conversation flow
- Only subagents that were actually created during the conversation are restored
- Orphan subagent folders (e.g., from crashed sessions) are not restored
- Nested subagents are handled correctly

### How It Works

1. Start by replaying only the root agent
2. When replaying messages, parse assistant messages for tool calls
3. When encountering a `🛠️[subagent ...]` tool call:
   - Publish `AgentStartedEvent` for the subagent (creates the tab)
   - Recursively replay that subagent's messages
   - When done, focus returns to parent context

### Implementation

The `HistoryReplayer` class in `simple_agent/application/history_replayer.py`:

```python
def replay_all_agents(self, starting_agent_id: AgentId) -> None:
    self._replay_agent(starting_agent_id)

def _replay_agent(self, agent_id: AgentId) -> None:
    messages = self._session_storage.load_messages(agent_id)
    # ... replay messages ...
    # When encountering subagent tool calls, recursively replay

def _process_subagent_calls(self, parent_agent_id: AgentId, content: str) -> None:
    parsed = parse_tool_calls(content, self._tool_syntax)
    for tool_call in parsed.tool_calls:
        if tool_call.name == "subagent":
            # Parse agent type from arguments
            # Create subagent ID
            # Publish AgentStartedEvent
            # Recursively replay subagent
```

## Tests

Tests are located in `tests/application/session_history_replay_test.py`:

- `test_continuing_session_replays_user_messages_as_events`
- `test_continuing_session_replays_assistant_messages_as_events`
- `test_continuing_session_replays_subagent_history`
- `test_continuing_session_restores_token_metadata`
- `test_subagent_restoration_follows_message_stream_order` - verifies correct event ordering
- `test_orphan_subagent_not_restored_without_tool_call` - verifies orphan subagents are ignored
