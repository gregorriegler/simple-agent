# Development Process

STARTER_SYMBOL=🔄

1. Read `goal.md` to understand the current state
2. Select the next example to implement from the task list.
    - If no examples remain in the current refined scenario, begin a new context using the prompt: "Read and follow the `process/refine-scenarios.md` instructions."
3. Look for the current TDD phase indicator in `goal.md`:
   - `## TDD Phase: 🔴` - need to write a failing test
   - `## TDD Phase: 🟢` - need to make a test pass
   - `## TDD Phase: 🧹` - need to refactor
4. Route to appropriate process:
   - 🔴: Create new context with "Read and follow `process/write-a-failing-test.md`"
   - 🟢: Create new context with "Read and follow `process/make-it-pass.md`"
   - 🧹: Create new context with "Read and follow `process/refactor.md`"
5. If no TDD phase is found in `goal.md`, default to RED phase and add `## TDD Phase: 🔴` to `goal.md`
6. After all phases are completed, check the example we were working on in the `goal.md` 
7. End this task creating a new context with the message: "Read and follow `process/development-process.md`
