# Refactoring Process

Refactoring means to improve the structure of the code in tiny steps while maintaining its current observable behavior. All the tests need to keep passing.

BE CONCISE!!

## 1. Find one thing to improve
1. Decide on something to improve.
    1. First look for production code that you can remove. Every single condition is a candidate for removal, if there is no test covering it.
    Get rid of that production code. 
    **Pay special attention to if statements and conditional expressions** that aren't exercised by any tests. These should be systematically identified and removed if no test requires them.
    If you are unsure whether you can remove production code, run a [mutation test](./mutation-test.md)
    1. Only if you can't find any production code that you can remove, start searching for code-smells using the [identify-code-smells](./identify-code-smells.md) process.
1. Break that improvement down into small atomic refactoring steps of which each step keeps all the tests passing
1. If there is already a `refactoring-plan.md` file, delete it.
1. Create a refactoring plan file `refactoring-plan.md` which lists all the steps as tasks prefixed with a checkbox.

## 2. Work through the planned tasks
For each task
1. Make sure all the tests pass before we start
1. make the change
1. Run the tests again to see everything still works
1. If any tests fail after your change, **immediately revert to the previous working state** before attempting a different approach. Never proceed with broken tests during refactoring.
1. commit only when I say its ok
1. check off the task
1. Go to the next step
