# Development Process

STARTER_SYMBOL=🔄

1. Read `goal.md` to understand the current state
2. Select the next example to implement from the task list.
    - If no examples remain in the current refined scenario, delegate through a fresh context that follows the `process/refine-scenarios.md` instructions.
3. Look for the current TDD phase indicator in `goal.md`:
   - `## TDD Phase: 🔴` - need to write a failing test
   - `## TDD Phase: 🟢` - need to make a test pass
   - `## TDD Phase: 🧹` - need to refactor
4. If no TDD phase indicator is found in `goal.md`, default to RED phase and add `## TDD Phase: 🔴` to `goal.md` and git commit it using an empty message and amending to the previous commit.
5. Route to appropriate process:
   - 🔴: Start a fresh context focused on reading and following `process/write-a-failing-test.md`.
   - 🟢: Start a fresh context focused on reading and following `process/make-it-pass.md`.
   - 🧹: Start a fresh context focused on reading and following `process/refactor.md` to improve the files <list-of-files> we are currently working on.
6. After the write a failing test phase is completed, set the phase indicator to 🟢 
7. After the make it pass phase is completed, check the example we were working on in the `goal.md`, set the phase indicator to 🧹 and amend commit this change keeping the existing commit message
8. After the refactoring phase is completed, set the phase indicator to 🔴 and amend commit this change keeping the existing commit message. Then delegate via a fresh context that reads and follows `process/development-process.md`.
