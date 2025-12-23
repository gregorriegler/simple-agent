# Event-to-Display Pipeline Simplification Analysis

## Problem Statement

Adding the `/clear` command required touching 7 files and creating parallel event/message hierarchies. The communication from domain events to the Textual display is overly complex.

## Current Architecture

### Legacy Flow (7 hops for `/clear`)

```
Agent.read_user_input_and_prompt_it()
    │ publishes
    ▼
SessionClearedEvent (events.py)
    │ subscribed in subscribe_events.py
    ▼
Display.clear(event) (display.py protocol)
    │ implemented by
    ▼
AgentDisplayHub.clear(event) (display_hub.py)
    │ delegates to
    ▼
TextualAgentDisplay.clear() (textual_display.py)
    │ posts
    ▼
SessionClearedMessage (textual_messages.py)
    │ handled by
    ▼
TextualApp.on_session_cleared_message() (textual_app.py)
    │ calls
    ▼
TextualApp.clear_agent_panels()
```

### Files Involved

| File | Role |
|------|------|
| `simple_agent/application/events.py` | Domain event definition (`SessionClearedEvent`) |
| `simple_agent/application/display.py` | Protocol defining `Display.clear(event)` and `AgentDisplay.clear()` |
| `simple_agent/infrastructure/subscribe_events.py` | Wires EventBus → Display |
| `simple_agent/infrastructure/display_hub.py` | Routes events to per-agent displays |
| `simple_agent/infrastructure/textual/textual_display.py` | Translates to Textual messages |
| `simple_agent/infrastructure/textual/textual_messages.py` | Textual message definition (`SessionClearedMessage`) |
| `simple_agent/infrastructure/textual/textual_app.py` | Actual UI update logic |

### The Core Problem: Two Messaging Systems

1. **Domain Events** (`SessionClearedEvent`) - pub/sub pattern via `SimpleEventBus`
2. **Textual Messages** (`SessionClearedMessage`) - Textual's internal message passing

Every domain event gets "translated" into a Textual message, creating parallel hierarchies:

| Domain Event | Textual Message |
|--------------|-----------------|
| `SessionClearedEvent` | `SessionClearedMessage` |
| `AssistantSaidEvent` | `AssistantSaysMessage` |
| `ToolCalledEvent` | `ToolCallMessage` |
| `ToolResultEvent` | `ToolResultMessage` |
| `UserPromptedEvent` | `UserSaysMessage` |

## Relevant Code

### events.py - Domain Event
```python
@dataclass
class SessionClearedEvent(AgentEvent):
    event_name: ClassVar[str] = "session_cleared"
```

### display.py - Protocol Methods
```python
class Display(Protocol):
    def clear(self, event) -> None:
        ...

class AgentDisplay(Protocol):
    def clear(self) -> None:
        ...
```

### subscribe_events.py - Wiring
```python
event_bus.subscribe(SessionClearedEvent, display.clear)
```

### display_hub.py - Routing
```python
def clear(self, event) -> None:
    agent = self._agent_for(event.agent_id)
    if agent:
        agent.clear()
```

### textual_display.py - Translation
```python
def clear(self):
    if self._app and self._app.is_running:
        self._app.post_message(SessionClearedMessage(self._log_id))
```

### textual_messages.py - Textual Message
```python
class SessionClearedMessage(Message):
    def __init__(self, log_id: str) -> None:
        super().__init__()
        self.log_id = log_id
```

### textual_app.py - Handler
```python
def on_session_cleared_message(self, message: SessionClearedMessage) -> None:
    self.clear_agent_panels(message.log_id)

def clear_agent_panels(self, log_id: str) -> None:
    # Clear chat scroll area
    try:
        chat_scroll = self.query_one(f"#{log_id}-scroll", VerticalScroll)
        chat_scroll.remove_children()
    except NoMatches:
        logger.warning("Could not find chat scroll #%s-scroll to clear", log_id)

    # Clear tool results panel
    tool_results_id = log_id.replace("log-", "tool-results-")
    try:
        tool_results = self.query_one(f"#{tool_results_id}", VerticalScroll)
        tool_results.remove_children()
        self._tool_result_collapsibles[tool_results_id] = []
        self._pending_tool_calls[tool_results_id] = {}
    except NoMatches:
        logger.warning("Could not find tool results #%s to clear", tool_results_id)
```

## Threading Model

### Normal Mode (main.py)
```python
async def run_session():
    await session.run_async(args, root_agent_id)

textual_app.run_with_session(run_session)
```

The session runs as an `asyncio.create_task()` inside Textual's event loop.

### Test Mode (main.py main_async)
```python
async with textual_app.run_test() as pilot:
    session_task = asyncio.create_task(run_session())
    await session_task
```

**Key insight:** Both modes now run in the same async context. `post_message()` works directly without thread-safety concerns in either mode.

## Proposed Simplification

### Option 1: Subscribe TextualApp Directly to Domain Events

Have `TextualApp` subscribe directly to domain events, eliminating the translation layer.

```python
# In subscribe_events or main.py
event_bus.subscribe(SessionClearedEvent, lambda e: app.post_message(e))
```

Then in `TextualApp`:
```python
def on_session_cleared_event(self, event: SessionClearedEvent) -> None:
    _, log_id, _ = self.panel_ids_for(event.agent_id)
    self.clear_agent_panels(log_id)
```

### What Gets Eliminated

| Layer | File | Can Remove |
|-------|------|------------|
| Textual Messages | `textual_messages.py` | `SessionClearedMessage` and similar |
| Agent Display method | `textual_display.py` | `clear()` method |
| Display Hub method | `display_hub.py` | `clear()` method |
| Protocol method | `display.py` | `Display.clear()`, `AgentDisplay.clear()` |

### The Catch: agent_id → log_id Mapping

`AgentDisplayHub` maintains `agent_id → AgentDisplay` mapping which knows `log_id`.

But `TextualApp` already has:
```python
@staticmethod
def panel_ids_for(agent_id: AgentId) -> tuple[str, str, str]:
    # Returns (tab_id, log_id, tool_results_id)
```

So `TextualApp` can derive panel IDs from `agent_id` directly.

### New Flow (3 hops)

```
Agent.read_user_input_and_prompt_it()
    │ publishes
    ▼
SessionClearedEvent (events.py)
    │ subscribed directly
    ▼
TextualApp.on_session_cleared_event() → clear_agent_panels()
```

## Implementation

Since both normal and test modes now run in the same async context, the implementation is straightforward.

**Current state:** the code already uses this pattern for the eleven migrated domain events—`subscribe_events.py` posts `DomainEventMessage` for each, and `TextualApp.on_domain_event_message()` renders them directly without per-event `TextualMessage` classes. Tab add/remove still uses Textual messages posted by `TextualDisplay`.

**Important:** Domain events are dataclasses, not Textual `Message` subclasses. To preserve hexagonal architecture (domain doesn't depend on infrastructure), we use a `DomainEventMessage` wrapper:

```python
# In textual_messages.py
class DomainEventMessage(Message):
    """Wrapper to post domain events to Textual without coupling domain to Textual."""
    def __init__(self, event) -> None:
        super().__init__()
        self.event = event

# In subscribe_events.py
event_bus.subscribe(SessionClearedEvent, lambda e: app.post_message(DomainEventMessage(e)))

# In textual_app.py - single handler dispatches by event type
def on_domain_event_message(self, message: DomainEventMessage) -> None:
    event = message.event
    if isinstance(event, SessionClearedEvent):
        _, log_id, _ = self.panel_ids_for(event.agent_id)
        self.clear_agent_panels(log_id)
```

This keeps domain events pure (no Textual dependency) while still eliminating the per-event Textual message classes.

## Events That Could Use This Pattern

| Domain Event | Current Textual Message | Simplify? |
|--------------|------------------------|-----------|
| `SessionClearedEvent` | `SessionClearedMessage` | Yes |
| `AssistantSaidEvent` | `AssistantSaysMessage` | Yes |
| `UserPromptedEvent` | `UserSaysMessage` | Yes |
| `ToolCalledEvent` | `ToolCallMessage` | Yes |
| `ToolResultEvent` | `ToolResultMessage` | Yes |
| `ToolCancelledEvent` | `ToolCancelledMessage` | Yes |
| `SessionInterruptedEvent` | `DomainEventMessage` | Yes (already migrated) |
| `SessionStartedEvent` | `DomainEventMessage` | Yes (already migrated) |
| `UserPromptRequestedEvent` | `DomainEventMessage` | Yes (already migrated) |
| `ErrorEvent` | `DomainEventMessage` | Yes (already migrated) |
| `AssistantRespondedEvent` | `DomainEventMessage` | Yes (already migrated) |
| `AgentStartedEvent` | `DomainEventMessage` | Yes |
| `AgentFinishedEvent` | `DomainEventMessage` | Yes |

## Trade-offs

### Pros
- Fewer files to touch for new events
- No parallel message hierarchies
- Less boilerplate code
- Direct path from domain to UI

### Cons
- `TextualApp` becomes aware of domain events (tighter coupling)
- Loses the `Display` protocol abstraction (harder to swap UI frameworks)

## Recommendation

For a single-UI codebase, **Option 1** is pragmatic. The `Display` protocol abstraction adds ceremony without providing real flexibility (you're not swapping Textual for another UI).

Keep domain events for:
- Logging (`EventLogger`)
- Persistence
- Cross-cutting concerns

But for UI updates, go direct: **EventBus → TextualApp**.

## Migration Plan: Atomic Steps

Migrate one event at a time. Each step keeps tests passing and avoids unused code.

### Pattern for Each Event Migration

Each event migration is a **single atomic commit** with two parts done together:

1. **Add** direct handler in `TextualApp` + wire subscription
2. **Remove** old path (Textual message, display methods, protocol methods, old subscription)

This avoids the intermediate state where both paths exist.

### Step-by-Step: `SessionClearedEvent` (First Migration) - THIS IS DONE

**Single commit that:**

1. **Add `DomainEventMessage` wrapper** in `textual_messages.py`:
   ```python
   class DomainEventMessage(Message):
       def __init__(self, event) -> None:
           super().__init__()
           self.event = event
   ```

2. **Add handler in `textual_app.py`:**
   ```python
   def on_domain_event_message(self, message: DomainEventMessage) -> None:
       event = message.event
       if isinstance(event, SessionClearedEvent):
           _, log_id, _ = self.panel_ids_for(event.agent_id)
           self.clear_agent_panels(log_id)
   ```

3. **Add subscription** (in `subscribe_events.py`):
   ```python
   event_bus.subscribe(SessionClearedEvent, lambda e: app.post_message(DomainEventMessage(e)))
   ```

4. **Remove from `textual_messages.py`:**
   - Delete `SessionClearedMessage` class

5. **Remove from `textual_app.py`:**
   - Delete `on_session_cleared_message()` handler

6. **Remove from `textual_display.py`:**
   - Delete `clear()` method

7. **Remove from `display_hub.py`:**
   - Delete `clear()` method

8. **Remove from `display.py`:**
   - Delete `Display.clear()` protocol method
   - Delete `AgentDisplay.clear()` protocol method

9. **Remove from `subscribe_events.py`:**
   - Delete `event_bus.subscribe(SessionClearedEvent, display.clear)`

**Tests pass. No dead code.**

### Subsequent Event Migrations

Apply the same pattern to each event:

| Order | Event | Removes | Status |
|-------|-------|---------|--------|
| 1 | `SessionClearedEvent` | `SessionClearedMessage`, `clear()` methods | DONE |
| 2 | `UserPromptedEvent` | `UserSaysMessage`, `user_says()` methods | DONE |
| 3 | `AssistantSaidEvent` | `AssistantSaysMessage`, `assistant_says()` methods | DONE |
| 4 | `ToolCalledEvent` | `ToolCallMessage`, `tool_call()` methods | DONE |
| 5 | `ToolResultEvent` | `ToolResultMessage`, `tool_result()` methods | DONE |
| 6 | `ToolCancelledEvent` | `ToolCancelledMessage`, `tool_cancelled()` methods | DONE |
| 7 | `SessionInterruptedEvent` | n/a (already direct) | DONE |
| 8 | `SessionStartedEvent` | `SessionStatusMessage`, `start_session()` methods | DONE |
| 9 | `UserPromptRequestedEvent` | `SessionStatusMessage`, `wait_for_input()` methods | DONE |
| 10 | `ErrorEvent` | `SessionStatusMessage`, `error_occurred()` methods | DONE |
| 11 | `AssistantRespondedEvent` | `UpdateTabTitleMessage`, `assistant_responded()` methods | DONE |

### After All Migrations

Once all events are migrated, including tab updates:

- `textual_messages.py` can be deleted entirely (or nearly)
- `display.py` protocols become minimal or removable
- `display_hub.py` becomes minimal or removable
- `textual_display.py` becomes minimal or removable

### Migration Checklist Template

For each event `XxxEvent`:

- [ ] Add handler branch in `on_domain_event_message()` in `textual_app.py`
- [ ] Add `event_bus.subscribe(XxxEvent, lambda e: app.post_message(DomainEventMessage(e)))`
- [ ] Delete `XxxMessage` from `textual_messages.py`
- [ ] Delete `on_xxx_message()` from `textual_app.py`
- [ ] Delete `xxx()` from `textual_display.py`
- [ ] Delete `xxx()` from `display_hub.py`
- [ ] Delete `xxx()` from `display.py` protocols
- [ ] Delete old subscription from `subscribe_events.py`
- [ ] Tests pass
