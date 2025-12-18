# Plan: /clear Command Implementation

## Design Decision

The `/clear` command will be intercepted in `Agent.read_user_input_and_prompt_it()` before the message is added to context and sent to the LLM. This is the simplest approach since there's no existing slash command infrastructure.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Agent.read_user_input_and_prompt_it()           │
│                                                              │
│  prompt = await self.user_input.read_async()                 │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────┐                                     │
│  │ Is it "/clear"?     │──Yes──► context.clear()             │
│  └─────────────────────┘         Publish confirmation event  │
│         │ No                     Return None (skip LLM)      │
│         ▼                                                    │
│  self.context.user_says(prompt)                              │
│  Continue to LLM...                                          │
└──────────────────────────────────────────────────────────────┘
```

## What Gets Cleared

- `agent.context` (the `Messages` object) - reset, preserving system prompt
- Session storage updated via `PersistedMessages.clear()`
- Agent type and session remain active

## Implementation Steps

### Step 1: Add `clear()` method to `Messages` class

**File:** `simple_agent/application/llm.py`

Add method to clear messages while preserving the system prompt:

```python
def clear(self):
    """Clear all messages except the system prompt."""
    if self._messages and self._messages[0].get("role") == "system":
        system_msg = self._messages[0]
        self._messages.clear()
        self._messages.append(system_msg)
    else:
        self._messages.clear()
```

**Test:** Verify `clear()` keeps system prompt, removes other messages.

### Step 2: Override `clear()` in `PersistedMessages` class

**File:** `simple_agent/application/persisted_messages.py`

Override to also persist the cleared state:

```python
def clear(self):
    super().clear()
    self._session_storage.save(self)
```

**Test:** Verify `clear()` persists to storage.

### Step 3: Handle `/clear` in Agent

**File:** `simple_agent/application/agent.py`

Modify `read_user_input_and_prompt_it()` to intercept `/clear`:

```python
async def read_user_input_and_prompt_it(self):
    prompt = await self.user_input.read_async()
    if prompt:
        if prompt.strip() == "/clear":
            self._handle_clear_command()
            return None  # Skip LLM call, continue loop
        self.context.user_says(prompt)
        self.event_bus.publish(UserPromptedEvent(self.agent_id, prompt))
    return prompt

def _handle_clear_command(self):
    self.context.clear()
    self.event_bus.publish(AssistantSaidEvent(
        self.agent_id,
        "Conversation cleared."
    ))
```

**Test:** Verify `/clear` clears context and publishes event.

### Step 4: Write tests

**Files:**
- `tests/application/llm_test.py` - Test `Messages.clear()`
- `tests/application/persisted_messages_test.py` - Test `PersistedMessages.clear()`  
- `tests/application/agent_test.py` - Test `/clear` handling in agent