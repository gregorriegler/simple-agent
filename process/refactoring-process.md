# Refactoring Process

Refactoring means to improve the structure of the code in tiny steps while maintaining its current observable behavior. All the tests need to keep passing.

## 1. Create a Plan
1. Decide on something to improve. If I don't tell you what to improve find something yourself using the [identify-code-smells](./identify-code-smells.md) process.
1. Break that improvement down into small atomic refactoring steps of which each step keeps all the tests passing
1. If there already is a `refactoring-plan.md` file, delete it.
1. Create a refactoring plan file `refactoring-plan.md` which lists all the steps as tasks prefixed with a checkbox.

## 2. Work through the planned tasks
For each task
1. Make sure all the tests pass before we start
1. make the change
1. Run the tests again to see everything still works
1. If it does not work, revert and try over
1. commit only when I say its ok
1. check off the task
1. Go to the next step 