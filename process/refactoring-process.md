# Refactoring Process

Refactoring means to improve the structure of the code in tiny steps while maintaining its current observable behavior. All the tests need to keep passing.

## 1. Create a Plan
1. Decide on something to improve
1. Break that improvement down in small atomic refactoring steps of which each step leaves the system working and all the tests passing
1. Create a temporary refactoring file `refactoring-plan.md` which contains all the steps each prefixed with a checkbox. Running the tests is not an explicit task on this list, because we DO IT FOR EVERY TASK!

## 2. Work through the planned tasks
For each task
1. Make sure all the tests pass before we start
1. make the change
1. Run the tests again to see everything still works
1. If it does not work, revert and try over
1. commit only when I say its ok
1. check off the task
1. Go to the next step 