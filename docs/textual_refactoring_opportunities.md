# Textual UI Refactoring Opportunities

This document identifies potential reusable **Textual Widgets** that can be extracted from the current monolithic `TextualApp`. The goal is to create self-contained UI components that encapsulate their own rendering and state, replacing the current "manager" style logic with composition of widgets.

## Proposed Components

### 1. `AgentWorkspace`
**Type**: Compound Widget (extends `Widget` or `Container`)
**Encapsulates**: The 3-pane layout logic currently in `create_agent_container`.
**Responsibilities**:
-   Composing the standard layout for an agent:
    -   Left Panel: Chat history (top) and Todo list (bottom).
    -   Right Panel: Tool execution log.
-   Managing the `ResizableHorizontal` and `ResizableVertical` splitters.
-   Exposing slots or methods to access the internal `ChatLog`, `TodoView`, and `ToolLog` widgets.

**Current implementation to replace**: `create_agent_container` method and the manual orchestration of `VerticalScroll`, `ResizableHorizontal`, and `ResizableVertical` in the main app.

### 2. `ChatLog`
**Type**: Widget (extends `VerticalScroll` or `Widget`)
**Encapsulates**: The display logic for conversation history.
**Responsibilities**:
-   Rendering "User" and "Assistant" messages.
-   Handling message formatting (Markdown, styling, attachments).
-   Auto-scrolling to the latest message.
-   Providing a clean API like `add_user_message(text, attachments)` and `add_assistant_message(text)`.

**Current implementation to replace**: The manual creation of `Markdown` widgets and the `write_message` method in `TextualApp`.

### 3. `ToolLog`
**Type**: Widget (extends `VerticalScroll` or `Widget`)
**Encapsulates**: The display and state management of tool executions.
**Responsibilities**:
-   Rendering the stream of tool calls and results.
-   Managing the "pending" state (loading spinners) for active tool calls.
-   Handling the complex logic of swapping "Call" widgets with "Result" widgets (success/error states, diff rendering).
-   Internalizing the `Collapsible` + `TextArea` + `Syntax` widget hierarchy for tool entries.
-   Providing an API like `add_call(call_id, tool_name)`, `complete_call(call_id, result)`, `cancel_call(call_id)`.

**Current implementation to replace**: `write_tool_call`, `write_tool_result`, `write_tool_cancelled`, `_pending_tool_calls`, and `_tool_result_collapsibles` logic.

### 4. `TodoView`
**Type**: Widget (extends `VerticalScroll` or `Widget`)
**Encapsulates**: The display of the agent's current Todo list.
**Responsibilities**:
-   Rendering the Todo markdown content.
-   Handling empty states (hiding the panel if no todos exist).
-   Providing an API like `update_content(markdown_text)`.

**Current implementation to replace**: `_load_todos`, `_refresh_todos`, `_todo_widgets`, and the logic toggling `display: none` on the container.

### 5. `SmartInput`
**Type**: Widget (extends `TextArea`)
**Encapsulates**: Input handling with autocomplete capabilities.
**Responsibilities**:
-   Capturing user input and submission events.
-   Managing the `AutocompletePopup` overlay.
-   Handling trigger detection (`/` for commands, `@` for files) and suggestion filtering.
-   Providing events for `Submitted` (with processed text and attachments) to the parent.

**Current implementation to replace**: `SubmittableTextArea` (refactored to be more self-contained and less coupled to the specific App instance).

## Benefits

-   **Composition over Management**: The main `TextualApp` becomes a simple coordinator that composes these widgets, rather than a manager that constantly reaches into UI internals.
-   **Testability**: Each widget (`ToolLog`, `ChatLog`) can be tested in isolation with unit tests (using `App.run_test` or `pilot`), ensuring rendering logic is correct without spinning up the full agent system.
-   **Reusability**: These components could be reused for different views (e.g., a "History View" or a "Debug View") without duplicating layout code.
