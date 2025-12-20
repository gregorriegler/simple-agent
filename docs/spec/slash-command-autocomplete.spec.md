# Slash Command Autocomplete

## Problem

When typing `/` in the input area, there's no way to discover available commands or their arguments. Users must memorize commands or guess.

## Solution

Create a command registry that the UI queries for autocomplete suggestions.

### Command Registry

```python
@dataclass
class SlashCommand:
    description: str
    arg_completer: Callable[[], list[str]] | None = None

commands = {
    "/clear": SlashCommand("Clear conversation history"),
    "/model": SlashCommand("Change model", arg_completer=get_available_models),
}
```

### Autocomplete Behavior

- Autocomplete activates only when input starts with `/`
- Typing `/` shows dropdown with all commands and descriptions
- Typing `/m` filters to matching commands
- Tab or click completes the selected command
- After `/model `, shows available model names from `arg_completer`
- Arrow keys navigate suggestions

### UI Changes

`SubmittableTextArea` in `textual_app.py`:
1. On text change, check if input starts with `/`
2. If yes, query registry for matching commands
3. Show dropdown below input area
4. Handle Tab for completion, arrows for navigation

### Relevant Files

- `simple_agent/application/agent.py` - current slash handling in `user_prompts()` (lines 71-89)
- `simple_agent/infrastructure/textual/textual_app.py` - `SubmittableTextArea`