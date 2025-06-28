# Refactoring Process

STARTER_SYMBOL=🧹

Refactoring means to improve the structure of the code in tiny steps while maintaining its current observable behavior. All the tests need to keep passing. Treat warnings as errors.

## 1. Identify things to improve
1. If there is already a `refactoring-plan.md` file, clean it so it's empty.
1. Find things to improve.
    - Remove Comments
    - Remove Dead code
    - Remove production code that is not exercised by any tests. If you are unsure whether you can remove production code, run a [mutation test](./mutation-test.md)
    - Fix Feature Envy
    - Identify and refactor duplicated code
    - Refactor Long Methods
    - Long Parameter Lists (more than 3 is long)
    - Long Classes
    - Long Files
    - Improve Names
1. Break that improvement down into small atomic refactoring steps of which each step keeps all the tests passing (use `test.sh`)
1. List all the steps as tasks prefixed with a checkbox in `refactoring-plan.md`.

## 2. Work through the planned tasks
For each task
1. Make sure all the tests pass before we start
1. Make sure there are no uncommitted changes before we start
1. Make the change/improvement
1. Run the tests again to see everything still works
1. If any tests fail after your change, revert the changes using `revert.sh`. Never proceed with broken tests during refactoring.
1. Check off the task
1. Commit the code using git. Refactoring commit messages start with an "r", e.g. "r extract class ..."
1. Go to the next step
