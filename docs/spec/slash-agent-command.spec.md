# Slash Command: /agent

## Problem Description
Users can already change model (`/model`) and clear context (`/clear`) during a live session. But they cannot switch the active agent profile (persona + tools + prompt) without restarting the session. Restarting loses flow and slows iteration.

We need an in-session way to switch agent profile while preserving the same live session identity and chat history.

## Functional Specification (WHAT)

### Scenario: Switch to a valid agent profile
**Given** the user is in an active chat session
**And** the `developer` agent exists
**When** the user types `/agent developer`
**Then** the active agent profile switches to `developer`
**And** future responses use the `developer` system prompt
**And** future tool calls use the `developer` tool set
**And** prior chat history remains available
**And** the system confirms `Switched to agent: developer`
**And** the system waits for the next user input

### Scenario: Switch to an unknown agent profile
**Given** the user is in an active chat session
**When** the user types `/agent nonexistent_agent`
**Then** the system shows `Agent 'nonexistent_agent' not found`
**And** the current agent profile remains unchanged

### Scenario: Autocomplete available agent profiles
**Given** the user types `/agent `
**Then** the system suggests available agent types

## Technical Solution (HOW)

### Design decisions
- Keep the same live `Agent` instance and `agent_id` (identity continuity).
- Reconfigure runtime parts in-place (name/type/model/tools/prompt), atomically.
- Reuse runtime assembly logic through a single builder/resolver seam.

### Preparatory refactoring (non-breaking)
1. Introduce `AgentRuntime` as a small value object that contains:
   - `agent_name`
   - `agent_type`
   - `model_name`
   - `tools`
   - `system_prompt`
2. Extract current runtime assembly from `AgentFactory.create_agent(...)` into a reusable builder method/service, e.g. `build_runtime(...) -> AgentRuntime`.
3. Keep behavior unchanged: `create_agent(...)` should consume `AgentRuntime` and build `Agent` exactly as today.

### Runtime switching
4. Add `Agent.change_agent(agent_type: str)` that:
   - requests a new `AgentRuntime` from the builder,
   - swaps runtime fields in-place (`agent_name`, `agent_type`, `llm`, `tools`, `tools_executor`),
   - reseeds the system prompt while preserving non-system messages,
   - publishes `AgentChangedEvent`.

### Slash command and autocomplete
5. Add `AgentCommand` to slash commands and visitor.
6. Register `/agent` in slash command registry with one required argument.
7. Add argument completion for `/agent` from available agent types.

### Events and UI
8. Add `AgentChangedEvent`.
9. Wire event serialization/persistence/subscriptions.
10. Update UI handling to reflect new agent name/type when this event is received.

### Implementation order (small safe steps)
1. Preparatory refactor + tests (no feature change).
2. Internal `change_agent(...)` behavior + tests.
3. `/agent` command parsing/execution + tests.
4. Autocomplete + tests.
5. Event/UI updates + tests.

### Files expected to change
- `docs/spec/slash-agent-command.spec.md`
- `simple_agent/application/agent_runtime.py` (new)
- `simple_agent/application/agent_factory.py`
- `simple_agent/application/agent.py`
- `simple_agent/application/slash_commands.py`
- `simple_agent/application/slash_command_registry.py`
- `simple_agent/application/events.py`
- `simple_agent/application/event_serializer.py`
- `simple_agent/infrastructure/subscribe_events.py`
- `simple_agent/infrastructure/textual/smart_input/autocomplete/slash_commands.py`
- `simple_agent/infrastructure/textual/widgets/agent_tabs.py`
