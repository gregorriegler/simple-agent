# Slash Clear Command

## Problem

There's no quick way to reset the conversation history while staying in the same agent session. Users must restart the application to get a fresh conversation.

## Solution

When the user types `/clear` in the chat input and submits it:
1. Clear the conversation history (the `Messages` object in `agent.context`)
2. Keep the current agent and session active
3. The user can continue chatting with a fresh context

### Relevant Code

- [simple_agent/application/agent.py](../../simple_agent/application/agent.py) - Agent class with `context: Messages` holding conversation
- [simple_agent/application/llm.py](../../simple_agent/application/llm.py) - `Messages` class definition
- [simple_agent/application/persisted_messages.py](../../simple_agent/application/persisted_messages.py) - Persisted messages wrapper

### Implementation Hint

The `/clear` input needs to be intercepted before being sent to the LLM. The `Messages` class (or `PersistedMessages`) needs a `clear()` method to reset the internal `_messages` list while preserving the system prompt.

### Out of Scope (for now)

- Autocomplete dropdown for slash commands
- Extensibility framework for adding more commands
- Other slash commands like `/model`