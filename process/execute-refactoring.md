## Execute a Planned Refactoring

STARTER_SYMBOL=🧹

1. Read the `refactoring-plan.md`
2. For each task
    1. Make sure all the tests pass before we start
    2. Make sure there are no uncommitted changes before we start
    3. Make the change/improvement
    4. Run the tests again to see everything still works
    5. If any tests fail after your change, revert the changes using `revert.sh`. Never proceed with broken tests during refactoring.
    6. Check off the task
    7. Commit the code using git. Refactoring commit messages start with an "r", e.g. "r extract class ..."
    8. Go to the next step in the `refactoring-plan.md`
    9. When all the refactorings are completed, initiate a new context with the prompt. "Write the next failing test `./process/write-a-failing-test.md`"
