# Plan: /model Command Implementation

## Design Overview

The key design change is that `Agent` needs access to `LLMProvider` to switch models at runtime, rather than just receiving a pre-instantiated `LLM`.

```
┌───────────────────────────────────────────────────────────────────┐
│                           Agent                                   │
│                                                                   │
│  user_prompts() loop                                              │
│       │                                                           │
│       ▼                                                           │
│  ┌──────────────────┐     ┌──────────────────────────────────┐    │
│  │ "/model <name>"  │────▶│ self.llm = llm_provider.get(name)│    │
│  │ "/model"         │────▶│ show error: Usage: /model <name> │    │
│  └──────────────────┘     └──────────────────────────────────┘    │
│                                                                   │
│  self.llm ◄─── Initially set from llm_provider.get(model_name)    │
│  self.llm_provider ◄─── NEW: injected dependency                  │
└───────────────────────────────────────────────────────────────────┘
```

## Key Decisions

1. **Agent receives LLMProvider instead of LLM** - Agent will instantiate its own LLM via `llm_provider.get(model_name)` and can switch by calling this again.

2. **Invalid model names** - Let `LLMProvider.get()` handle errors (raise ValueError). The Agent catches and displays the error.

3. **Event notification** - Publish a new `ModelChangedEvent` so UI can display confirmation.

## Implementation Steps

### Step 1: Add ModelChangedEvent
Add a new event class to notify when the model changes.
- File: `simple_agent/application/events.py`
- Add: `ModelChangedEvent(agent_id, old_model, new_model)`

### Step 2: Modify Agent to accept LLMProvider
Change Agent's constructor to accept `LLMProvider` + initial model name instead of just `LLM`.
- File: `simple_agent/application/agent.py`
- Add: `llm_provider` parameter
- Add: `model_name` parameter (or get from agent definition)
- Change: `self.llm` is now set via `self.llm_provider.get(model_name)`

### Step 3: Handle /model command in user_prompts()
Add logic to parse and handle `/model` command alongside existing `/clear`.
- File: `simple_agent/application/agent.py`
- In `user_prompts()`:
  - Parse `/model <name>` → switch model
  - Parse `/model` (no args) → show usage error
  - Publish `ModelChangedEvent` on success

### Step 4: Update AgentFactory
Modify `AgentFactory.create_agent()` to pass `llm_provider` to Agent.
- File: `simple_agent/application/agent_factory.py`
- Pass `self._llm_provider` to Agent constructor
- Pass model name from agent definition

### Step 5: Add test for /model command
Write test that verifies model switching works.
- File: `tests/slash_model_command_test.py`
- Test: `/model` shows usage error
- Test: `/model claude-3-haiku` switches model
- Test: conversation history is preserved after switch