# Goal: Add optional starting_prompt to agent definitions

## Context
Currently, when starting an agent without a user message (e.g., `./agent.sh` or `🛠️ subagent development`), the agent waits for user input. For agents like `development`, we want them to start working immediately.

## Solution
Add an optional `starting_prompt` field to agent definition front matter. When an agent starts without a user message, use this prompt instead.

## Implementation Notes
- Modify agent definition loading to parse `starting_prompt` from front matter
- Modify agent initialization to use starting_prompt when no user message provided
- Keep it simple: treat starting_prompt exactly like a user message
- No special logging or display needed

## Acceptance Criteria
- Agent definitions can include optional `starting_prompt` in front matter
- Starting prompt is used when no user message is provided
- User message always takes precedence over starting prompt
- Works for both main agents and subagents
- Empty or missing starting_prompt preserves current behavior

## TDD Plan
## TDD Phase: 🔴

## Checklist
- [ ] Scenario 1: Agent with starting_prompt and no user message
- [ ] Scenario 2: Agent with starting_prompt but user provides message
- [ ] Scenario 4: Subagent with starting_prompt and no task description
- [ ] Scenario 5: Empty starting_prompt is treated as no prompt

## Scenarios

### Scenario 1: Agent with starting_prompt and no user message - REFINED
**Given** an agent definition with:
```yaml
---
starting_prompt: "Review todo.md and start working on the next task"
---
```
**When** the agent starts without a user message
**Then** it should use "Review todo.md and start working on the next task" as the user message

### Scenario 2: Agent with starting_prompt but user provides message - REFINED
**Given** an agent definition with:
```yaml
---
starting_prompt: "Review todo.md and start working on the next task"
---
```
**When** the agent starts with user message "Fix the bug in session.py"
**Then** it should use "Fix the bug in session.py" (user message takes precedence)

### Scenario 4: Subagent with starting_prompt and no task description - REFINED
**Given** a development agent with starting_prompt
**When** spawned via `🛠️ subagent development` (no task description)
**Then** it should use the starting_prompt as the task

### Scenario 5: Empty starting_prompt is treated as no prompt - REFINED
**Given** an agent definition with:
```yaml
---
starting_prompt: ""
---
```
**When** the agent starts without a user message
**Then** it should wait for user input (empty string = no prompt)
