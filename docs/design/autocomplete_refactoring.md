# Autocomplete Design Analysis

## Current State (NOW)

The current Autocomplete implementation relies on `SmartInput` (inheriting from `TextArea`) acting as the central orchestrator. It manages the lifecycle of the `AutocompletePopup`, handles all key events (for both editing and navigation), and directly invokes the `Autocompleter`.

### ASCII Diagram (NOW)

```
+-----------------------------------------------------------------------------------+
|                                     SmartInput                                    |
|                                                                                   |
|  [ _on_key ] --------------------------------------------------------+            |
|       | (Tab/Enter/Up/Down/Esc)                                      |            |
|       v                                                              |            |
|  [ AutocompletePopup ] <-------(manages lifecycle & nav)-------------+            |
|       ^                                                              |            |
|       | (uses)                                                       |            |
|  [ CompletionSearch ] <--------(returns)-------------------- [ Autocompleter ]    |
|       ^                                                              ^            |
|       | (executes async)                                             | (checks)   |
|       +--------------------------------------------------------------+            |
|                                                                                   |
|  [ FileContextExpander ] (for submission)                                         |
|  [ _referenced_files ]   (state)                                                  |
+-----------------------------------------------------------------------------------+
```

### Responsibilities (NOW)

| Component | Responsibilities |
| :--- | :--- |
| **SmartInput** | - Handles all user input (text editing + navigation).<br>- Manages `AutocompletePopup` lifecycle (create, mount, remove).<br>- Calculates popup anchor position (`CaretScreenLocation`).<br>- Triggers autocomplete checks on every keypress.<br>- Forwards navigation keys to the popup manually.<br>- Applies completion results to the text.<br>- Manages `_referenced_files` state. |
| **Autocompleter** | - Logic strategy to determine if autocomplete should trigger.<br>- Returns a `CompletionSearch` protocol. |
| **CompletionSearch** | - Encapsulates the async logic to retrieve `Suggestion`s.<br>- `Popup` calls this directly. |
| **AutocompletePopup** | - Renders the list of suggestions.<br>- Executes the `CompletionSearch`.<br>- Maintains internal selection state.<br>- **Note:** Has `move_selection_down` methods called by `SmartInput`. |

### Design Issues & Unnecessary Complications

1.  **Coupling in `SmartInput` (God Class)**: `SmartInput` knows too much. It is coupled to the *lifecycle* of the popup, the *navigation logic* of the popup (forwarding keys), and the *execution flow* of the search.
2.  **Split Responsibilities**: The logic for "What to show" (Search) and "How to show it" (Popup) is intertwined. The `Popup` executes the search, which binds the UI widget to the data retrieval mechanism.
3.  **Manual Event Routing**: `SmartInput` explicitly checks `if self.popup: ...` for every navigation key. This makes `_on_key` cluttered and hard to extend.
4.  **Geometry Logic Leakage**: `SmartInput` calculates screen coordinates (`CaretScreenLocation`) to anchor the popup. This view-layout logic cluttering the input widget.
5.  **State Management**: `SmartInput` manages the `_referenced_files` set, but this state is implicitly updated by side-effects of applying a completion.

---

## Desirable Design (Refactored)

The goal is to separate the **Controller** (coordination), the **View** (Input & Popup), and the **Model** (Autocompleter/Suggestions). `SmartInput` should return to being primarily a text editor, while a new `AutocompleteController` handles the complexity.

### ASCII Diagram (DESIRABLE)

```
+---------------------+           +-----------------------------+
|    SmartInput       |<--------->|   AutocompleteController    |
| (TextArea + Events) | (Attached)|                             |
+---------------------+           |  [ Autocompleter ] (Model)  |
         ^                        |  [ PopupManager ]  (UI Logic)|
         | (Updates Text)         +-------------+---------------+
         |                                      | (Controls)
         |                                      v
+---------------------+           +-----------------------------+
| FileContextExpander |           |     AutocompletePopup       |
| (Independent Helper)|           |      (Dumb Display)         |
+---------------------+           +-----------------------------+
```

### Responsibilities (DESIRABLE)

| Component | Responsibilities |
| :--- | :--- |
| **SmartInput** | - **Primary:** Text editing surface.<br>- **Role:** Emits events (e.g., `CursorMoved`, `TextChanged`) or allows Controller to hook into `_on_key`.<br>- **State:** Holds text and `_referenced_files`.<br>- **Action:** Accepts "Apply Completion" commands from Controller. |
| **AutocompleteController** | - **Primary:** Coordinator.<br>- **Role:** Listens to `SmartInput`.<br>- **Logic:** Calls `Autocompleter.check()`.<br>- **Action:** Executes the search (async) and updates the Popup.<br>- **Action:** Intercepts navigation keys (Up/Down/Tab) when Popup is active.<br>- **Action:** Calculates anchor position.<br>- **Action:** Updates `SmartInput` when a suggestion is selected. |
| **Autocompleter** | - **Primary:** Pure Logic/Model.<br>- **Role:** Determines *what* to suggest based on context.<br>- **Output:** Returns `List[Suggestion]` or a Future (decoupled from UI). |
| **AutocompletePopup** | - **Primary:** Dumb View.<br>- **Role:** Display a list of strings/items.<br>- **API:** `set_items()`, `select_next()`, `select_prev()`, `get_selected()`.<br>- **Note:** No longer executes search or manages async tasks. |

### Key Improvements

1.  **Decoupling**: `SmartInput` no longer knows about `AutocompletePopup`'s internal API. It just works with a Controller.
2.  **Testability**: The `AutocompleteController` can be unit tested without a full Textual app by mocking `SmartInput` and `Autocompleter`.
3.  **Simplified Popup**: The `AutocompletePopup` becomes a generic "List Picker" widget that can be reused or easily replaced.
4.  **Clean Event Flow**: Key events are intercepted by the Controller only when relevant, keeping `SmartInput`'s `_on_key` clean.
