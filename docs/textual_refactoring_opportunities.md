# Textual UI Refactoring Opportunities

This document analyzes the current responsibilities of the Textual UI layer (`simple_agent/infrastructure/textual/`) and proposes potential components for extraction to improve modularity, testability, and maintainability.

## Existing Responsibilities

### `TextualApp` (in `textual_app.py`)
Currently, `TextualApp` acts as a "God Class" for the UI, handling:
-   **Application Lifecycle**: Startup, shutdown, session management.
-   **Layout Management**: Composing the main screen, managing tabs.
-   **Agent State Management**: Tracking active agents, their tabs, logs, and tool outputs.
-   **Event Handling**: Receiving `DomainEventMessage` and dispatching to specific UI update logic.
-   **Tool Output Rendering**: Creating and managing widgets for tool calls and results (Collapsibles, TextAreas, Syntax highlighting).
-   **Todo List Management**: Loading and updating todo widgets.
-   **Loading Animations**: Managing the loading spinner state.

### `SubmittableTextArea` (in `textual_app.py`)
This class extends `TextArea` and handles:
-   **Input Submission**: Capturing Enter/Ctrl+Enter.
-   **Autocomplete Orchestration**: Detecting triggers (`/`, `@`), managing the `AutocompletePopup` visibility and positioning.
-   **Autocomplete Navigation**: Handling key events (Tab, Up, Down, Escape) to navigate suggestions.
-   **Data Fetching**: Querying `SlashCommandRegistry` and `FileSearcher`.
-   **File Context Management**: Tracking referenced files to be sent with the prompt.

## Potential Components for Extraction

### 1. `AgentTabManager`
**Responsibility**: Encapsulate the creation, storage, and lifecycle management of agent tabs.
-   **Logic to Extract**: `create_agent_container`, `add_subagent_tab`, `remove_subagent_tab`, `_ensure_agent_tab_exists`, `update_tab_title`, and associated state (`_agent_panel_ids`, `_agent_names`, `_todo_widgets`, `_tool_results_to_agent`).
-   **Benefits**: Decouples the main app from the specific layout details of agent panels. Makes it easier to change the tab layout or add new per-agent UI elements.

### 2. `ToolOutputRenderer`
**Responsibility**: Handle the creation and update of tool call and result widgets.
-   **Logic to Extract**: `write_tool_call`, `write_tool_result`, `write_tool_cancelled`, `_pop_pending_tool_call`, and related state (`_pending_tool_calls`, `_tool_result_collapsibles`).
-   **Benefits**: Centralizes the complex logic of rendering different tool result types (diffs vs text) and managing the collapsible state. Simplifies `TextualApp`.

### 3. `AutocompleteController`
**Responsibility**: Manage the logic for autocomplete triggering, filtering, and selection.
-   **Logic to Extract**: `_check_autocomplete`, `_show_autocomplete`, `_show_file_autocomplete`, `_navigate_autocomplete`, `_complete_selection`, `_hide_autocomplete`.
-   **Benefits**: `SubmittableTextArea` becomes purely about input handling. The autocomplete logic (which involves async searching and state machine logic) becomes testable in isolation without a full UI harness.

### 4. `FileContextManager`
**Responsibility**: Manage the resolution of referenced files into prompt context.
-   **Logic to Extract**: Logic within `action_submit_input` that reads files and formats the XML context, and `get_referenced_files`.
-   **Benefits**: Separates IO operations (reading files) from the UI event handler. Allows reusing this logic if other input methods are added.

### 5. `DomainEventDispatcher`
**Responsibility**: Map domain events to UI actions.
-   **Logic to Extract**: The large `if/elif` block in `on_domain_event_message`.
-   **Benefits**: The `TextualApp` shouldn't need to know about every single domain event. A dispatcher can route events to the appropriate manager (e.g., routing `AgentStartedEvent` to `AgentTabManager`, `ToolResultEvent` to `ToolOutputRenderer`).

## Summary of Proposed Architecture

-   **`TextualApp`**: Coordinates the high-level components and runs the main loop.
-   **`AgentTabManager`**: "I know how to add/remove/update agent tabs."
-   **`ToolOutputRenderer`**: "I know how to display tool inputs and outputs."
-   **`AutocompleteController`**: "I know when to show suggestions and what they are."
-   **`SubmittableTextArea`**: "I handle user typing and delegation to the controller."
