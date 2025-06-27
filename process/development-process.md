# Development Process

STARTER_SYMBOL=🛠️

Your answers should be succinct and concise

1. Identify where we are
    - Read the `goal.md` file with the list of examples
1. Pick the first item of the examples that is not yet implemented
1. Make sure the system has at least a walking skeleton for the feature we are building in place. If that's not case, we'll build the walking skeleton with this first example.
1. Write a failing test for it. The test should be the simplest most possible test that drives the desired change.
1. Run `test.sh` which runs all tests, and see it fail
    1. Be aware, that if its a Verify or approvaltests test, the first test will always fail because there is no verified file yet. Only in this case, you have to consider if the received file is what you would expect and approve it.
    1. If it passes, you found a test that does not drive any change in production code. So we don't need the test. Remove it from the examples, and remove the test again. Find another test that forces a change in production code.
1. Implement the smallest possible change to make it pass
1. Run all tests, and see it pass
1. Ask me to commit the code
1. Refactor the code using the [refactoring process](./refactoring-process.md).
1. Check off the item in the examples
1. Go to 2