# Development Process

STARTER_SYMBOL=🔄

1. Read `goal.md` to understand the current state
2. Select the next example to implement from the task list.
    - If no examples remain in the current refined scenario, begin a new context using the prompt: "Read and follow the `process/refine-scenarios.md` instructions."
3. Look for the current TDD phase indicator in `goal.md`:
   - `## TDD Phase: 🔴` - need to write a failing test
   - `## TDD Phase: 🟢` - need to make a test pass
   - `## TDD Phase: 🧹` - need to refactor
4. If no TDD phase indicator is found in `goal.md`, default to RED phase and add `## TDD Phase: 🔴` to `goal.md` and git commit it using an empty message and amending to the previous commit.
5. Route to appropriate process:
   - 🔴: Create new context with "Read and follow `process/write-a-failing-test.md`"
   - 🟢: Create new context with "Read and follow `process/make-it-pass.md`"
   - 🧹: Create new context mode saying "Read and follow `process/refactor.md` to improve the files <list-of-files> we are currently working on"
6. After the write a failing test phase is completed, set the phase indicator to 🟢 
7. After the make it pass phase is completed, check the example we were working on in the `goal.md`, set the phase indicator to 🧹 and amend commit this change keeping the existing commit message
8. After the refactoring phase is completed, set the phase indicator to 🔴 and amend commit this change keeping the existing commit message. Then end this task creating a new context with the message: "Read and follow `process/development-process.md`
