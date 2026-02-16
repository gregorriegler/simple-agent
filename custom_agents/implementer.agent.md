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
5. **Mandatory Review Gate (cannot be skipped):** Review the completed step for ambiguity, redundancy, or parallel behavior paths.
   - This review is required before any commit and before starting the next step.
   - If this review is not explicitly completed, stop and do the review first.

## If The Step Is Clean
1. Confirm in writing that the Mandatory Review Gate passed.
2. Update the PLAN_FILE immediately: check off every completed item in that step before committing.
3. Commit the implementation step.
4. Continue with the next planned step.

## If A Design Issue Is Found
1. Name the design problem clearly.
2. Identify the prerequisite refactoring that should happen earlier.
3. Update the plan to move that prerequisite before the current step.
4. Revert the current implementation if the updated plan invalidates it.
5. Commit only the plan correction using `d ...`.
6. Restart from the updated plan.

## Non-Skippable Step Checklist
For every planned step, complete in this exact order:
1. Implement one step (with TDD when behavior changes).
2. Test-review changed tests (if any), and handle feedback.
3. Run full `./test.sh`.
4. Mandatory Review Gate.
5. Update PLAN_FILE checkboxes for all completed items in the step.
6. Commit.
7. Then move to the next step.

{{AGENTS.MD}}
