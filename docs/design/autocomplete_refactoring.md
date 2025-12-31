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

1.  **Split Responsibilities**: The `Autocompleter` (Factory) vs `CompletionSearch` (Product) split is over-engineered for simple use cases. It forces a two-step "Check then Search" dance even when not needed.
2.  **Popup Logic Leakage**: The `AutocompletePopup` is responsible for executing the search (`search.get_suggestions()`), which couples the View to the Data Retrieval logic.
3.  **Complex Protocols**: The `Autocompleter` protocol definition is confusing and unnecessarily separates the trigger check from the suggestion retrieval.
4.  **Coupling**: `SmartInput` is intimately aware of `AutocompletePopup`'s internal state (checking `if self.popup.suggestion_list` in event handlers).

---

## Desirable Design (Refactored)

The goal is to simplify the architecture by consolidating logic into a **Self-Contained SmartInput Widget** that owns a **Dumb AutocompletePopup**. We will replace the complex Protocol interactions with a **Single Protocol** that handles both triggering and suggestion retrieval.

### ASCII Diagram (DESIRABLE)

```
+------------------------------------------------------------------+
|                           SmartInput                             |
|                    (Self-Contained Widget)                       |
|                                                                  |
|  [ _on_key ] ------------------------+                           |
|       |                              | (Control Flow)            |
|       v                              v                           |
|  [ AutocompleteStrategy ]      [ AutocompletePopup ]             |
|  (Single Protocol)             (Dumb View)                       |
|       ^                              ^                           |
|       | (Data)                       | (Display)                 |
|       +------------------------------+                           |
|                                                                  |
+------------------------------------------------------------------+
```

### Responsibilities (DESIRABLE)

| Component | Responsibilities |
| :--- | :--- |
| **SmartInput** | - **Primary:** The public widget user interacts with.<br>- **Logic:** Orchestrates input, checks strategy, controls popup.<br>- **Action:** Calls `strategy.suggest()`. If suggestions found -> `popup.show()`.<br>- **Action:** On Up/Down/Tab -> `popup.select_next()` etc.<br>- **Action:** On Enter -> `popup.get_selection()` -> Apply to text. |
| **AutocompleteStrategy** | - **Primary:** Single Protocol for logic.<br>- **Contract:** `async def suggest(cursor) -> List[Suggestion] | None`.<br>- **Behavior:** Returns `None` if not triggered (e.g. wrong prefix), returns `List` (empty or populated) if triggered.<br>- **Implementations:** `SlashCommandStrategy`, `FileSearchStrategy`, `CompositeStrategy`. |
| **AutocompletePopup** | - **Primary:** Dumb View.<br>- **Contract:** Small API: `show(items, anchor)`, `hide()`, `select_next()`, `get_selection()`.<br>- **Behavior:** Just renders the list given to it. Does not know about strategies or searching. |

### Key Improvements

1.  **Single Protocol**: Collapses `Autocompleter` and `CompletionSearch` into one `AutocompleteStrategy`. simpler to implement and understand.
    *   *Signature:* `async def suggest(self, context) -> Optional[List[Suggestion]]`
    *   Implementations can perform fast sync checks (e.g., prefix matching) before awaiting IO.
2.  **Self-Contained Widget**: `SmartInput` encapsulates the complexity. Consumers just instantiate `SmartInput`.
3.  **Dumb View**: `AutocompletePopup` is strictly a UI component. It doesn't run async tasks or business logic.
4.  **Reduced Coupling**: `SmartInput` passes data to `Popup`. `Popup` returns selection to `SmartInput`. No shared state or deep probing.
