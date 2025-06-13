STARTER_SYMBOL=🧹

When you refactor always start your answer with the STARTER_SYMBOL (🧹)

# Refactoring Process

Refactoring means to improve the structure of the code in tiny steps while maintaining its current observable behavior. All the tests need to keep passing. Treat warnings as errors.

## 1. Identify things to improve
1. If there is already a `refactoring-plan.md` file, clean it so its empty.
1. Find things to improve.
    - Remove Comments
    - Remove Dead code
    - Remove Production code is not exercised by any tests. If you are unsure whether you can remove production code, run a [mutation test](./mutation-test.md)
    - Fix Feature Envy
    - Identify and refactor duplicated code
    - Refactor Long Methods
    - Long Parameter Lists (more than 3 is long)
    - Long Classes
    - Long Files
    - Improve Names
1. Break that improvement down into small atomic refactoring steps of which each step keeps all the tests passing (use `test.sh`)
1. Lists all the steps as tasks prefixed with a checkbox in `refactoring-plan.md`.

## 2. Work through the planned tasks
For each task
1. Make sure all the tests pass before we start
1. make the change
1. Run the tests again to see everything still works
1. If any tests fail after your change, **immediately revert to the previous working state** before attempting a different approach. Never proceed with broken tests during refactoring.
1. commit the code
1. check off the task
1. Go to the next step
