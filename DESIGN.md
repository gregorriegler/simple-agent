# Design Document: Per-Agent Input Isolation

## 1. Objective
The goal is to move the `SmartInput` widget from the global application scope into each `AgentWorkspace` (tab). This ensures that input is visually associated with a specific agent and functionally routed to that agent, resolving the ambiguity of "which agent am I talking to?".

## 2. Problem Analysis
Currently, `TextualApp` creates a single `SmartInput` instance that is shared across all agent tabs.
- **Visual Ambiguity**: It is not visually distinct which agent the input belongs to.
- **Functional Ambiguity**: Input submission goes to a global queue in `TextualUserInput`. If multiple agents are running (e.g., main agent waiting for sub-agent), input typed in the "Main Agent" tab could theoretically be consumed by the "Sub Agent" if the system isn't careful, or vice versa. The user expectation is that input in Tab A goes to Agent A.

## 3. Proposed Design

### 3.1. Frontend (UI Structure)

#### 3.1.1. `AgentWorkspace` Restructuring
The `AgentWorkspace` widget will be refactored to contain the input field.
- **Inheritance Change**: `AgentWorkspace` currently inherits from `ResizableHorizontal`. It will be changed to inherit from `Vertical` (or `Widget` with vertical layout) to accommodate the vertical stacking of the main content area (split view) and the input area.
- **Composition**:
  ```python
  class AgentWorkspace(Vertical):
      def compose(self):
          # The split view (Chat + Tools)
          with ResizableHorizontal(id="workspace-split"):
               yield self.left_panel
               yield self.tool_log
          # The input field
          yield self.smart_input
  ```
- **Styling**: The `SmartInput` inside the workspace will retain the `dock: bottom` (or similar flex layout) to sit at the bottom of the tab.

#### 3.1.2. `AgentTabs` Updates
- `AgentTabs` is responsible for creating `AgentWorkspace`. It must now pass the necessary dependencies for `SmartInput` (specifically the `SuggestionProvider`) to `AgentWorkspace`.

#### 3.1.3. `TextualApp` Updates
- **Remove Global Input**: The single `SmartInput` in `TextualApp.compose` will be removed.
- **Event Handling**: `TextualApp` listens for `SmartInput.Submitted`. Since there are multiple inputs now, it must identify the source.
  - The event will bubble up from the specific `AgentWorkspace`.
  - `TextualApp` can determine the `agent_id` from the `AgentWorkspace` that triggered the event.
  - It will then call `self.user_input.submit_input(content, agent_id)`.

### 3.2. Backend (Input Routing)

#### 3.2.1. `MultiplexedUserInput` Protocol
We will introduce a new protocol (or extend the existing concept) to support targeted reading/writing.
- Define `MultiplexedUserInput(Protocol)`:
  ```python
  class MultiplexedUserInput(UserInput):
      async def read_for_agent(self, agent_id: AgentId) -> str: ...
      def submit_input(self, text: str, agent_id: AgentId) -> None: ...
  ```

#### 3.2.2. `TextualUserInput` Implementation
- `TextualUserInput` will implement `MultiplexedUserInput`.
- It will maintain a dictionary of queues: `self.queues: dict[AgentId, Queue]`.
- `submit_input(text, agent_id)` will push to the specific agent's queue.
- `read_for_agent(agent_id)` will await the specific agent's queue.

#### 3.2.3. `ScopedUserInput` Adapter
- A new adapter class `ScopedUserInput` will be created.
- It wraps a `MultiplexedUserInput` (the shared instance) and an `agent_id`.
- It implements the standard `UserInput` protocol (`read_async`).
  ```python
  class ScopedUserInput(UserInput):
      def __init__(self, base: MultiplexedUserInput, agent_id: AgentId): ...
      async def read_async(self) -> str:
          return await self.base.read_for_agent(self.agent_id)
  ```

#### 3.2.4. `AgentFactory` Integration
- When creating an `Agent`, `AgentFactory` will wrap the global `user_input` in a `ScopedUserInput` (if the global input supports multiplexing).
- This ensures the `Agent` (application logic) remains unchanged but unknowingly reads from its dedicated channel.

## 4. Implementation Plan

1.  **Backend Core**:
    *   Define `MultiplexedUserInput` protocol in `simple_agent/application/user_input.py`.
    *   Implement `MultiplexedUserInput` in `TextualUserInput`.
    *   Create `ScopedUserInput` in `simple_agent/application/scoped_user_input.py`.
    *   Update `AgentFactory` to apply scoping.

2.  **Frontend Layout**:
    *   Refactor `AgentWorkspace` to be a `Vertical` container holding the `ResizableHorizontal` split and `SmartInput`.
    *   Update `AgentTabs` to pass `SuggestionProvider` to `AgentWorkspace`.
    *   Update `TextualApp` to create `SuggestionProvider` and pass it to tabs, but remove global `SmartInput`.

3.  **Frontend Logic**:
    *   Update `TextualApp.on_smart_input_submitted` to extract `agent_id` from the event source and call `submit_input(text, agent_id)`.
    *   Ensure focus is managed correctly when switching tabs (focus the input of the active tab).

4.  **Cleanup & Verification**:
    *   Update CSS for scoped input fields.
    *   Fix tests (`AgentWorkspace` tests, `TextualApp` tests, Golden Masters).

## 5. Verification
- **Manual Verification**: Run the app, open multiple tabs. Type in Tab A, verify Agent A gets it. Switch to Tab B, type, verify Agent B gets it.
- **Automated Tests**:
  - Unit tests for `TextualUserInput` multi-queue logic.
  - Unit tests for `ScopedUserInput`.
  - Integration tests ensuring `AgentWorkspace` renders correctly and events propagate.
