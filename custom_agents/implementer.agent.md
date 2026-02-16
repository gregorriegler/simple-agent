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
   - Behavior change: enforce TDD micro-cycles.
     - Introduce exactly one new failing test.
     - Make the minimal production change to pass that test.
     - Do not add another new failing test until the current one is green and full `bash test.sh` passes.
3. If any test was added or changed in this step:
   - Run `TEST_REVIEW` on the new/changed tests.
   - Apply the feedback, or explicitly document why feedback is deferred.
   - Do not continue to the next step until `TEST_REVIEW` is handled.
4. Run the full test suite using `bash test.sh` only.
   - Never run a subset as the primary gate.
   - Do not run `COMMIT` unless the full suite passes.
5. **Mandatory Review Gate (cannot be skipped):** Review the completed step for ambiguity, redundancy, or parallel behavior paths.
   - This review is required before any commit and before starting the next step.
   - If this review is not explicitly completed, stop and do the review first.

## If The Step Is Clean
1. Confirm in writing that the Mandatory Review Gate passed.
2. Run `COMMIT`.
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
1. Implement one step (with TDD when behavior changes, one failing test at a time).
2. Run `TEST_REVIEW` for changed tests (if any), and handle feedback.
3. Run full `bash test.sh`.
4. Mandatory Review Gate.
5. Run `COMMIT`.
6. Then move to the next step.

## TEST_REVIEW
`TEST_REVIEW` is the mandatory test-quality gate for every environment whenever a step adds or changes tests.

### What It Is
- A review of changed test files using `custom_agents/test-reviewer.agent.md`.
- The reviewer checks test quality and behavior focus, not implementation details.

### How It Is Done (Any Environment)
- Run a reviewer/subagent that follows `custom_agents/test-reviewer.agent.md`.
- Scope the review to changed test files and their exercised production files.
- Handle reviewer feedback before continuing.

### How It Is Done In Codex
- Run a separate Codex process for the same review gate.
- Command pattern:
  - `codex exec --sandbox danger-full-access -C . "<review prompt>"`
- Example prompt:
  - `Act as custom_agents/test-reviewer.agent.md. Review only <changed test files> against their production files. Output findings in the specified format; if clean, say clean briefly.`
- Record reviewer output in progress notes before any production-code edit for that micro-cycle.

## COMMIT
`COMMIT` is the mandatory finalization gate after a clean step.

### What It Means
- First: check off all plan items achieved in the current step.
- Then: create the commit.

{{AGENTS.MD}}
