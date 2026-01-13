# Design Document: Per-Agent Input Isolation

## 1. Objective
The goal is to move the `SmartInput` widget from the global application scope into each `AgentWorkspace` (tab). This ensures that input is visually associated with a specific agent and functionally routed to that agent, resolving the ambiguity of "which agent am I talking to?".

## 2. Problem Analysis
Currently, `TextualApp` creates a single `SmartInput` instance and a single `TextualUserInput` (queue) that is shared across all agent tabs.
- **Visual Ambiguity**: It is not visually distinct which agent the input belongs to.
- **Functional Ambiguity (Cross-Talk)**: Input is submitted to a single global queue. If multiple agents are running (e.g., a main agent and a sub-agent), input typed in the "Main Agent" tab could be consumed by the "Sub Agent" (or vice versa) because they both read from the same source.
- **Requirement**: Input submitted in Tab A must *only* be received by Agent A. Input submitted in Tab B must *only* be received by Agent B.

## 3. Proposed Design

### 3.1. Frontend (UI Structure)

#### 3.1.1. `AgentWorkspace` Restructuring
The `AgentWorkspace` widget will be refactored to contain its own `SmartInput` instance.
- **Composition**: The `AgentWorkspace` will stack the split view (Chat + Tools) and the `SmartInput` vertically.
  ```python
  class AgentWorkspace(Vertical):
      def compose(self):
          # The split view
          with ResizableHorizontal(id="workspace-split"):
               yield self.left_panel
               yield self.tool_log
          # The dedicated input field
          yield self.smart_input
  ```

#### 3.1.2. `TextualApp` & `AgentTabs` Updates
- **Remove Global Input**: The single `SmartInput` in `TextualApp` is removed.
- **Event Handling**: `TextualApp` listens for `SmartInput.Submitted` events bubbling up from `AgentWorkspace`.
  - The event source allows identifying the `agent_id`.
  - `TextualApp` uses this ID to route the text to the correct backend channel.

### 3.2. Backend (Input Routing via Factory)

Instead of a complex "multiplexing" protocol, we will use a **Factory Pattern** to provide each Agent with its own dedicated `UserInput` instance. This creates multiple independent channels rather than one shared channel.

#### 3.2.1. `UserInputFactory` Protocol
We introduce a factory protocol in the application layer to decouple Agent creation from input mechanism details.
```python
class UserInputFactory(Protocol):
    def create_user_input(self, agent_id: AgentId) -> UserInput: ...
```

#### 3.2.2. `TextualUserInputFactory` Implementation
In the infrastructure layer, we implement this factory to manage `TextualUserInput` instances.
- **Registry**: It maintains a `dict[AgentId, TextualUserInput]`.
- **Creation**: `create_user_input(agent_id)` creates a new `TextualUserInput` (which wraps a simple `Queue`), stores it in the registry, and returns it.
- **Access**: `TextualApp` uses the registry to find the correct `UserInput` instance when the UI submits text for a specific agent.

#### 3.2.3. `AgentFactory` Refactoring
- **Dependency Change**: `AgentFactory` will accept `UserInputFactory` instead of a single `UserInput` object.
- **Logic**: When creating an agent (or sub-agent), it calls `self.user_input_factory.create_user_input(agent_id)` to provision a dedicated input channel for that agent.

## 4. Implementation Plan

1.  **Backend Core**:
    *   Define `UserInputFactory` protocol in `simple_agent/application/user_input_factory.py`.
    *   Refactor `AgentFactory` to use `UserInputFactory`.
    *   Update `Session` to accept `UserInputFactory`.

2.  **Infrastructure**:
    *   Implement `TextualUserInputFactory` in `simple_agent/infrastructure/textual/textual_user_input_factory.py`.
    *   Update `TextualApp` to initialize the factory and pass it to the Session.
    *   Update `TextualApp` logic: When `on_smart_input_submitted` occurs, look up the `agent_id`'s input channel via the factory and submit the text.

3.  **Frontend Layout**:
    *   Move `SmartInput` inside `AgentWorkspace`.
    *   Pass `SuggestionProvider` dependencies down to `AgentWorkspace` (via `AgentTabs`).

4.  **Verification**:
    *   Verify that typing in Agent A's tab does not trigger input in Agent B's reading loop.
    *   Verify that multiple agents can exist with independent input states.
