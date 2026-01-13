# Agent Task Manager Specification

## 1. Problem Statement

Currently, the application's user interface allows for multiple agents to run concurrently in different tabs. However, user-initiated interrupts (via the `Escape` key) only affect the main agent that was started with the session.

This is because sub-agents are spawned as new, independent `asyncio.Task` instances that are not tracked by the main application (`TextualApp`). The `Escape` key handler is hardwired to cancel only the primary session task, leaving all other agent tasks running.

The desired behavior is for the `Escape` key to interrupt the agent running in the currently active tab.

## 2. Proposed Solution

We will introduce a new, centralized class called `AgentTaskManager` to manage the lifecycle of all agent-related asynchronous tasks. This manager will act as the single source of truth for all running agents, allowing for targeted control over each one.

## 3. `AgentTaskManager` Class Design

The `AgentTaskManager` class will be responsible for creating, registering, and canceling agent tasks.

### Core Data Structure

The manager will use a dictionary to map an `AgentId` to its corresponding `asyncio.Task` instance.

```python
self._tasks: dict[AgentId, asyncio.Task] = {}
```

### Methods

-   **`start_task(self, agent_id: AgentId, coroutine: Coroutine) -> asyncio.Task`**:
    -   Creates a new `asyncio.Task` from the provided coroutine.
    -   Registers the task in the `_tasks` dictionary with its `agent_id`.
    -   Adds a `done_callback` to the task to automatically remove it from the dictionary upon completion, preventing memory leaks.
    -   Returns the newly created task.

-   **`cancel_task(self, agent_id: AgentId) -> bool`**:
    -   Looks up the task associated with the given `agent_id`.
    -   If a task is found, it calls the task's `.cancel()` method.
    -   Logs a warning if no task is found for the given ID.
    -   Returns `True` if a task was found and cancellation was attempted, `False` otherwise.

-   **`cancel_all_tasks(self)`**:
    -   Iterates through all tasks in the `_tasks` dictionary and cancels each one.
    -   This is useful for a clean application shutdown.

## 4. Phased Integration Plan

This integration will be done in two phases to manage complexity.

### 4.1. Phase 1: Root Agent Integration

The initial goal is to manage only the main, root agent's task. This will validate the `AgentTaskManager`'s role within the application's core lifecycle.

**4.1.1. Instantiation and Dependency Injection**
1.  A single instance of `AgentTaskManager` will be created in `simple_agent/main.py`.
2.  This instance will be passed to the `TextualApp`.

**4.1.2. Refactoring `TextualApp`**
The main session task will be started and managed by the `AgentTaskManager`.
1.  **In `on_mount`**: The main session runner task will be started via `agent_task_manager.start_task(self._root_agent_id, self._run_session())`. The `self._session_task` variable will be removed.
2.  **In `on_key` (for the `Escape` key)**:
    -   The logic will be updated to get the active `AgentId` from the `AgentTabs` widget.
    -   It will then call `self.agent_task_manager.cancel_task(active_agent_id)`.
    -   The old logic of canceling `self._session_task` will be completely removed.

**4.1.3. Milestone: End-to-End Verification**
Before proceeding to Phase 2, manual End-to-End (E2E) testing must be performed to confirm the successful integration for the root agent.

**Verification Steps:**
1.  Run the application with a task for the root agent.
2.  While the agent is running, press the `Escape` key.
3.  **Expected Outcome:** The root agent's task should be immediately cancelled, and the application should shut down cleanly.

Only after this behavior is confirmed will Phase 2 (Sub-agent Integration) begin.

### 4.2. Phase 2: Sub-agent Integration (Future Work)

Once the root agent is managed correctly, the system will be extended to manage sub-agents.

**4.2.1. Dependency Injection**
1. The `AgentTaskManager` instance will be passed down to the `Session` object and subsequently to the `AgentFactory`.

**4.2.2. Refactoring `AgentFactory`**
The `create_spawner` method within `AgentFactory` will be modified. Instead of calling `asyncio.create_task()` directly, it will now use the task manager:

```python
# Before
asyncio.create_task(subagent.start())

# After
agent_task_manager.start_task(agent_id, subagent.start())
```

This phased approach ensures a clean separation of concerns, provides the desired user experience, and makes the overall architecture more robust and maintainable.