# Implementation Plan: Slash Command Autocomplete

Plans out the spec in `docs/spec/slash-command-autocomplete.spec.md`

## Design Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              textual_app.py - SubmittableTextArea               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  on_text_changed() ──▶ SlashCommandRegistry.match(text)  │  │
│  │  Tab key ──▶ complete selected command                   │  │
│  │  Shows dropdown with matching commands                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              SlashCommandRegistry (NEW - application layer)     │
│  - commands: dict[str, SlashCommand]                            │
│  - get_all_commands() -> list[str]                              │
│  - get_matching_commands(prefix: str) -> list[SlashCommand]     │
└─────────────────────────────────────────────────────────────────┘
```

## Current State Analysis

- Slash commands are parsed in `agent.py` within `user_prompts()` method (lines ~71-89)
- Commands `/clear` and `/model` are handled with if/elif chains
- UI is Textual-based in `simple_agent/infrastructure/textual/textual_app.py`
- `SubmittableTextArea` is where user types input

## Key Design Decisions

1. **SlashCommandRegistry in application layer** - Domain logic for commands, UI-agnostic
2. **SlashCommand dataclass** - Holds command name, description, and optional arg_completer
3. **Autocomplete in SubmittableTextArea** - Textual-specific UI implementation
4. **Dropdown widget for suggestions** - Custom Textual widget or use existing patterns

## Implementation Steps

### Step 1: Create SlashCommandRegistry with SlashCommand dataclass

Create a registry that holds all slash commands with their metadata.

**Test first**: Write a test that verifies the registry returns `/clear` and `/model` commands and can filter by prefix.

**Files to create**:
- `tests/application/slash_command_registry_test.py` (NEW)
- `simple_agent/application/slash_command_registry.py` (NEW)

---

### Step 2: Refactor existing slash command handling to use registry

Move the command definitions from `agent.py` to use the registry, keeping behavior unchanged.

**Test first**: Existing tests in `slash_model_command_test.py` and `slash_clear_command_test.py` should still pass.

**Files to modify**:
- `simple_agent/application/agent.py`

---

### Step 3: Add autocomplete UI to SubmittableTextArea

Implement the autocomplete dropdown in the Textual UI:
- Listen for text changes starting with `/`
- Show dropdown with matching commands
- Handle Tab for completion
- Handle arrow keys for navigation

**Test first**: Write a test for the autocomplete behavior (may require Textual testing patterns).

**Files to modify**:
- `simple_agent/infrastructure/textual/textual_app.py`
- `tests/infrastructure/textual/textual_autocomplete_test.py` (NEW)

---

### Step 4: Manual verification

Verify autocomplete works in the running application:
- Type `/` - shows all commands with descriptions
- Type `/m` - filters to `/model`
- Tab completes the selected command
- Arrow keys navigate suggestions

---

## Out of Scope (LATER)

- Argument completion (e.g., `/model <model_name>`)
- Custom agent type completion for `/agent` command
- Fuzzy matching for typos
