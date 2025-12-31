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

1.  **`CompletionTrigger`** (formerly Autocompleter)
    *   **Responsibility:** Pure Logic. Determines *if* the context is valid for this feature.
    *   **Signature:** `is_triggered(cursor_context) -> bool`
    *   *Examples:* `PrefixTrigger("@")`, `RegexTrigger("...")`, `StartOfLineTrigger`.

2.  **`SuggestionProvider`** (formerly CompletionSearch)
    *   **Responsibility:** Pure Data. Fetches items when requested.
    *   **Signature:** `async fetch(cursor_context) -> List[Suggestion]`
    *   *Examples:* `FileProvider`, `SlashCommandProvider`, `HistoryProvider`.

### Composition (The "Rule")

These two are combined into a configuration object (a Rule or Feature), decoupling the *When* from the *What*.

`AutocompleteRule(trigger=StartOfLineTrigger(), provider=SlashCommandProvider())`

### ASCII Diagram (DESIRABLE)

```
+-----------------------------------------------------------------------+
|                             SmartInput                                |
|                      (Self-Contained Widget)                          |
|                                                                       |
|  [ Config/Rules ]                                                     |
|       |                                                               |
|       +-> [ Rule A: (Trigger A) + (Provider A) ]                      |
|       +-> [ Rule B: (Trigger B) + (Provider B) ]                      |
|                                                                       |
|  [ Logic Flow ]                                                       |
|       |                                                               |
|       v                                                               |
|  1. Iterate Rules -> if rule.trigger.is_triggered(cursor):            |
|       |                                                               |
|       +-> 2. active_provider = rule.provider                          |
|       +-> 3. suggestions = await active_provider.fetch()              |
|       +-> 4. popup.show(suggestions)                                  |
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
| **SmartInput** | - **Orchestrator:** Holds the list of `AutocompleteRule`s.<br>- **Event Loop:** On keypress, checks `rules`. If match found, invokes `provider`.<br>- **UI Control:** Manages the `AutocompletePopup` (show/hide/nav). |
| **CompletionTrigger** | - **Contract:** `is_triggered(Context) -> bool`.<br>- **Role:** Reusable logic (e.g., generic "Word starts with X" trigger). |
| **SuggestionProvider** | - **Contract:** `async fetch(Context) -> List`.<br>- **Role:** Domain logic (e.g., "Get files", "Get Git branches"). |
| **AutocompleteRule** | - **Role:** A simple container/struct binding a `Trigger` to a `Provider`. |
| **AutocompletePopup** | - **Contract:** `show(items)`, `select_next()`, `get_selection()`.<br>- **Role:** Dumb view. |

### Key Improvements

1.  **Orthogonality:** You can combine `StartOfLineTrigger` with *any* provider (e.g., Slash Commands, or maybe a Macro list). You can reuse `FileProvider` with different triggers (e.g., `@` or `file:`).
2.  **Clarity:** Names `Trigger` and `Provider` clearly describe the two distinct phases of the operation.
3.  **Simplicity:** `SmartInput` just iterates a list. Adding a new feature is just appending a `Rule` to the list.
