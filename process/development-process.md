# Development Process State Machine

STARTER_SYMBOL=🔄

This process reads the current state from `goal.md` and routes to the appropriate TDD phase.

## Process

1. Read `goal.md` to understand current state
2. Look for the current TDD phase indicator in `goal.md`:
   - `## TDD Phase: 🔴` - need to write a failing test
   - `## TDD Phase: 🟢` - need to make a test pass
   - `## TDD Phase: 🧹` - need to refactor
3. Route to appropriate process:
   - 🔴: Create new context with "Read and follow `process/write-a-failing-test.md`"
   - 🟢: Create new context with "Read and follow `process/make-it-pass.md`"
   - 🧹: Create new context with "Read and follow `process/refactor.md`"
4. If no TDD phase is found in `goal.md`, default to RED phase and add `## TDD Phase: 🔴` to `goal.md`
5. After the SubTask is completed, change to the next phase and initiate the next context.
