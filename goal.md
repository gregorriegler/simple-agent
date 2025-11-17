# Goal: Add optional starting_prompt to agent definitions

## Context
Currently, when starting an agent without a user message (e.g., `./agent.sh` or `🛠️ subagent development`), the agent waits for user input. For agents like `development`, we want them to start working immediately.

## Solution
Add an optional `starting_prompt` field to agent definition front matter. When an agent starts without a user message, use this prompt instead.

## Scenarios

### Scenario 1: Agent with starting_prompt and no user message
**Given** an agent definition with:
```yaml
---
starting_prompt: "Review todo.md and start working on the next task"
---
```
**When** the agent starts without a user message
**Then** it should use "Review todo.md and start working on the next task" as the user message

### Scenario 2: Agent with starting_prompt but user provides message
**Given** an agent definition with:
```yaml
---
starting_prompt: "Review todo.md and start working on the next task"
---
```
**When** the agent starts with user message "Fix the bug in session.py"
**Then** it should use "Fix the bug in session.py" (user message takes precedence)

### Scenario 3: Agent without starting_prompt and no user message
**Given** an agent definition without a `starting_prompt` field
**When** the agent starts without a user message
**Then** it should wait for user input (current behavior)

### Scenario 4: Subagent with starting_prompt and no task description
**Given** a development agent with starting_prompt
**When** spawned via `🛠️ subagent development` (no task description)
**Then** it should use the starting_prompt as the task

### Scenario 5: Empty starting_prompt is treated as no prompt
**Given** an agent definition with:
```yaml
---
starting_prompt: ""
---
```
**When** the agent starts without a user message
**Then** it should wait for user input (empty string = no prompt)

## Implementation Notes
- Modify agent definition loading to parse `starting_prompt` from front matter
- Modify agent initialization to use starting_prompt when no user message provided
- Keep it simple: treat starting_prompt exactly like a user message
- No special logging or display needed

## Acceptance Criteria
- [ ] Agent definitions can include optional `starting_prompt` in front matter
- [ ] Starting prompt is used when no user message is provided
- [ ] User message always takes precedence over starting prompt
- [ ] Works for both main agents and subagents
- [ ] Empty or missing starting_prompt preserves current behavior

## TDD Plan

### Step 1: Parse starting_prompt from agent definition - DRAFT
**Test**: `test_agent_definition_parses_starting_prompt`
- Given an agent definition YAML with `starting_prompt: "some prompt"`
- When parsing the agent definition
- Then the `starting_prompt` field should be accessible

**Test**: `test_agent_definition_handles_missing_starting_prompt`
- Given an agent definition YAML without `starting_prompt`
- When parsing the agent definition
- Then the `starting_prompt` should be None or empty

**Test**: `test_agent_definition_handles_empty_starting_prompt`
- Given an agent definition YAML with `starting_prompt: ""`
- When parsing the agent definition
- Then the `starting_prompt` should be empty string

### Step 2: Use starting_prompt when no user message provided - DRAFT
**Test**: `test_uses_starting_prompt_when_no_user_message`
- Given an agent with starting_prompt "Review todo.md"
- When initializing agent with no user message
- Then first message should be "Review todo.md"

**Test**: `test_user_message_overrides_starting_prompt`
- Given an agent with starting_prompt "Review todo.md"
- When initializing agent with user message "Fix bug"
- Then first message should be "Fix bug"

**Test**: `test_waits_for_input_when_no_starting_prompt_and_no_message`
- Given an agent without starting_prompt
- When initializing agent with no user message
- Then should wait for user input (return None or raise appropriate signal)

### Step 3: Integration with subagent spawning - DRAFT
**Test**: `test_subagent_uses_starting_prompt_when_no_task_description`
- Given development agent with starting_prompt
- When spawning via subagent tool without task description
- Then subagent should start with starting_prompt

**Test**: `test_subagent_task_description_overrides_starting_prompt`
- Given development agent with starting_prompt
- When spawning via subagent tool with task description
- Then subagent should use task description

### Step 4: End-to-end validation - DRAFT
**Integration Test**: Create a test agent definition with starting_prompt and verify it works through the full agent lifecycle
- [ ] Unit tests cover all scenarios