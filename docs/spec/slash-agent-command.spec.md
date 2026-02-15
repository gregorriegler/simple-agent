# Slash Command: /agent

## Problem Description
Users often start a session with a default agent but realize mid-conversation they need a different agent (e.g., switching from `default` to `developer`). Currently, they must restart the session, losing context. They need a way to switch agent personas and capabilities on the fly while preserving chat history.

## Functional Specification (WHAT)

### Scenario: Switch to a valid agent
**Given** the user is in a chat session with the `default` agent
**And** the `developer` agent exists
**When** the user types `/agent developer`
**Then** the system switches the active agent to `developer`
**And** the system prompt is updated to the `developer` agent's prompt
**And** the available tools are updated to the `developer` agent's tools
**And** the chat history is preserved
**And** the system confirms "Switched to agent: developer"
**And** the system waits for the next user input (does not auto-reply)

### Scenario: Switch to an invalid agent
**Given** the user is in a chat session
**When** the user types `/agent nonexistent_agent`
**Then** the system displays an error message "Agent 'nonexistent_agent' not found"
**And** the active agent remains unchanged

### Scenario: Autocomplete agent names
**Given** the user types `/agent `
**Then** the system suggests a list of available agent types

## Technical Solution (HOW)

### 1. Agent Class Updates
- Implement `Agent.change_agent(agent_type: str)` method.
- This method needs to:
  - Load the new agent definition (system prompt, tools).
  - Update `self.agent_type` and `self.agent_name`.
  - Update `self.tools` (ToolLibrary).
  - Update `self.context` by replacing the existing system message with the new one.
  - Publish `AgentChangedEvent`.

### 2. Slash Command Implementation
- Create `AgentCommand` in `simple_agent/application/slash_commands.py`.
- Register it in `simple_agent/application/slash_command_registry.py`.
- Implement `SlashCommandVisitor.change_agent(command: AgentCommand)`.

### 3. Tool Library & Factory
- Ensure `ToolLibrary` can be re-initialized or hot-swapped.
- Ensure `AgentFactory` or similar can load an agent definition by name without creating a full new `Agent` instance, or extract the loading logic to a helper.

### 4. Events
- Create `AgentChangedEvent` in `simple_agent/application/events.py`.
- Handle this event in the UI (if necessary) to update the displayed agent name.

### Prerequisite Steps
- Verify `AgentFactory` exposes a way to get agent configuration (prompt, tools) by name.

### Files to Modify
- `simple_agent/application/agent.py`
- `simple_agent/application/slash_commands.py`
- `simple_agent/application/slash_command_registry.py`
- `simple_agent/application/events.py`
- `simple_agent/infrastructure/textual/smart_input/autocomplete/slash_commands.py` (for autocomplete provider)