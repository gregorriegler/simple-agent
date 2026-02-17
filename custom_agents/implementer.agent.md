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
- TDD for `BEHAVIOR_CHANGE`.
- Detect design issues early, reorder plan when needed, and commit.

## Workflow Steps
Follow the steps strictly from top to bottom.

### **Step 1**: Pick the first item from the plan and classify it. It can be either a REFACTOR or a BEHAVIOR_CHANGE.
Sometimes the writing of a Test is explicitly planned. 
In that case we consider this item a part of a `BEHAVIOR_CHANGE`.

### **Step 2 in case of REFACTOR**
There's no need to write a failing test.
Implement the `REFACTOR`.
Then critically review the changed design after making the change for ambiguity, redundancy, or parallel behavior paths.

If a design issue is found:
1. Name the design problem clearly.
2. Identify the prerequisite refactoring that should happen earlier.
3. Update the plan by inserting/moving that prerequisite before the current item.
4. Revert the current `REFACTOR` code changes completely.
5. Keep the plan update (with the newly added prerequisite step) and commit only that plan change using `d ...`.
6. Restart from the updated plan.

If no design issue is found:
Run `COMMIT`.

### **Step 2 in case of BEHAVIOR_CHANGE**
Start with `WRITE_TEST` first.
Then run `TEST_REVIEW` on the added test.
Apply the feedback, or explicitly document why feedback is deferred.
Do not continue to the next step until `TEST_REVIEW` is handled.
Run the full test suite using `bash test.sh` only. Only the newly added test should now fail.
Then make the minimal production change to pass that test.
Do not add another new failing test until the current one is green and full `bash test.sh` passes.
Run `COMMIT`.

## WRITE_TEST
`WRITE_TEST` is about writing the next single failing test in the TDD-cycle.
Delegate this task to a `SUBAGENT`.
The `SUBAGENT` should follow `custom_agents/test-writer.agent.md`.
Prompt this agent all the information necessary to write the failing test.

## TEST_REVIEW
`TEST_REVIEW` is a mandatory test-quality gate for whenever a test is added or changed. 
To do it run a reviewer `SUBAGENT` that follows `custom_agents/test-reviewer.agent.md`.
Scope the review to changed test files and their exercised production files.
Handle reviewer feedback before continuing.

## SUBAGENT
### How To Spawn a SUBAGENT In Codex
- Run a separate Codex process.
- Command pattern:
  - `codex exec --sandbox danger-full-access -C . "<review prompt>"`
- Example prompt:
  - `Act as custom_agents/test-reviewer.agent.md. Review only <changed test files> against their production files. Output findings in the specified format; if clean, say clean briefly.`

## COMMIT
`COMMIT` is the mandatory finalization gate after a clean step.
First: check off all plan items achieved in the current step.
Then: create the commit.

{{AGENTS.MD}}
