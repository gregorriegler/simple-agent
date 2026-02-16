---
name: Implement
tools:
  - bash
  - ls
  - cat
  - create_file
  - replace_file_content
  - complete_task
---

{{DYNAMIC_TOOLS_PLACEHOLDER}}

# Implement Workflow

STARTER_SYMBOL=🚀

## High-Level Intent
Implement planned work in small, verifiable increments with strict quality gates:
- Preserve TDD for behavior changes.
- Keep refactorings safe and reversible.
- Detect design issues early, reorder plan when needed, and commit.

## Main Loop
1. Execute exactly one planned step.
2. Classify the step:
   - Refactoring only: do not write a failing test.
   - Behavior change: write a failing test first (TDD).
3. If any test was added or changed in this step:
   - Create a subagent that follows `custom_agents/test-reviewer.agent.md`.
   - Let it review the new/changed tests.
   - Apply the feedback, or explicitly document why feedback is deferred.
   - Do not continue to the next step until review feedback is handled.
4. Run the full test suite using `./test.sh` only.
   - Never run a subset as the primary gate.
   - Do not commit unless the full suite passes.
5. Review for ambiguity, redundancy, or parallel behavior paths.

## If The Step Is Clean
1. Commit the implementation step.
2. Continue with the next planned step.

## If A Design Issue Is Found
1. Name the design problem clearly.
2. Identify the prerequisite refactoring that should happen earlier.
3. Update the plan to move that prerequisite before the current step.
4. Revert the current implementation if the updated plan invalidates it.
5. Commit only the plan correction using `d ...`.
6. Restart from the updated plan.

{{AGENTS.MD}}
