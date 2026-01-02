# Autocomplete Design Analysis

## Current State (NOW)

The current implementation uses two protocols, `Autocompleter` and `CompletionSearch`, coupled via a **Factory Pattern**.

1.  **Autocompleter (The "When"):** Responsible for detecting *if* autocomplete should start.
2.  **CompletionSearch (The "What"):** Responsible for retrieving the suggestions.

Currently, `Autocompleter.check()` returns a `CompletionSearch` instance. This tightly couples the detection logic to the retrieval logic (e.g., `SlashCommandAutocompleter` must know how to instantiate `SlashCommandSearch`).

### ASCII Diagram (NOW)

```
+-------------------------------------------------------+
|                      SmartInput                       |
|                                                       |
|  [ Autocompleter ] (Factory)                          |
|         |                                             |
|         +---(check)--> [ Returns CompletionSearch ] --+
|                               |                       |
|                               v                       |
|                     [ AutocompletePopup ]             |
|                               |                       |
|                               +--(get_suggestions)--> [ Suggestion List ]
+-------------------------------------------------------+
```

### Design Issues

*   **Coupling:** The Trigger (`Autocompleter`) creates the Provider (`CompletionSearch`). You cannot easily reuse "Start of line detection" with a different "Data Source" without subclassing.
*   **Naming:** `Autocompleter` and `CompletionSearch` are generic and don't clearly convey "Trigger" vs "Provider".

---

## Desirable Design (Refactored)

We will separate the concerns into two **Orthogonal Protocols** with descriptive names, wired together via composition (e.g., a list of Rules/Features) rather than factory methods.

### New Protocols

1.  **`AutocompleteTrigger`** (formerly Autocompleter)
    *   **Responsibility:** Pure Logic. Determines *if* the autocomplete process should start (i.e., triggering the search and identifying the active feature).
    *   **Signature:** `is_triggered(cursor_and_line) -> bool`
    *   *Examples:* `SlashAtStartOfLineTrigger`, `AtSymbolTrigger`, `ColonTrigger`.

2.  **`SuggestionProvider`** (formerly CompletionSearch)
    *   **Responsibility:** Pure Data. Fetches items when requested.
    *   **Signature:** `async fetch(cursor_and_line) -> List[Suggestion]`
    *   *Examples:* `FileProvider`, `SlashCommandProvider`, `HistoryProvider`.

### Composition (The "Rule")

These two are combined into a configuration object (a Rule or Feature), decoupling the *When* from the *What*.

`SingleAutocompleteRule(trigger=SlashAtStartOfLineTrigger(), provider=SlashCommandProvider())`

The `AutocompleteRule` is now a Protocol defining a `async check(cursor_and_line) -> List[Suggestion]` method.
- `SingleAutocompleteRule` implements this for a single trigger/provider pair: if triggered, it awaits the provider's fetch; otherwise returns empty list.
- `AutocompleteRules` implements this as a Composite, iterating through a list of rules and returning the first non-empty list of suggestions.

### ASCII Diagram (DESIRABLE)

```
+-----------------------------------------------------------------------+
|                             SmartInput                                |
|                      (Self-Contained Widget)                          |
|                                                                       |
|  [ AutocompleteRules ] (Composite)                                    |
|       |                                                               |
|       +-> [ SingleRule A: (Trigger A) + (Provider A) ]                |
|       +-> [ SingleRule B: (Trigger B) + (Provider B) ]                |
|                                                                       |
|  [ Logic Flow ]                                                       |
|       |                                                               |
|       v                                                               |
|  1. suggestions = await rules.check(cursor_and_line)                  |
|       |                                                               |
|       +-> 2. if suggestions:                                          |
|       +-> 3. popup.show(suggestions)                                  |
|                                                                       |
+--------------------------+--------------------------------------------+
                           |
                           v
                 [ AutocompletePopup ]
                    (Dumb Display)
```

### Responsibilities (DESIRABLE)

| Component | Responsibilities |
| :--- | :--- |
| **SmartInput** | - **Orchestrator:** Holds the `AutocompleteRules` composite.<br>- **Event Loop:** On keypress, awaits `rules.check()`. If suggestions returned, shows popup.<br>- **UI Control:** Manages the `AutocompletePopup` (show/hide/nav). |
| **AutocompleteTrigger** | - **Contract:** `is_triggered(cursor_and_line) -> bool`.<br>- **Role:** Reusable logic (e.g., "Line starts with /"). |
| **SuggestionProvider** | - **Contract:** `async fetch(cursor_and_line) -> List`.<br>- **Role:** Domain logic (e.g., "Get available slash commands"). |
| **SingleAutocompleteRule** | - **Role:** A concrete implementation of `AutocompleteRule` Protocol binding a `Trigger` to a `Provider`. Returns suggestions directly. |
| **AutocompleteRules** | - **Role:** Composite implementation of `AutocompleteRule` that checks a list of rules. |
| **AutocompletePopup** | - **Contract:** `show(items)`, `select_next()`, `get_selection()`.<br>- **Role:** Dumb view. |

### Key Improvements

1.  **Orthogonality:** You can combine `SlashAtStartOfLineTrigger` with *any* provider.
2.  **Honest Naming:** `cursor_and_line` describes exactly what data is passed. `AutocompleteTrigger` describes exactly what feature is being triggered.
3.  **Simplicity:** `SmartInput` just iterates a list. Adding a new feature is just appending a `Rule` to the list.
