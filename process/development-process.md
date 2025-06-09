# Development Process

1. Identify where we are
    - Read the `goal.md` file with the testlist
1. Pick the first item of the Testlist that is not yet implemented
1. Write a failing test for it
1. Run `test.sh` which runs all tests, and see it fail
    1. If it passes, you found a test that does not drive any change in production code. So we don't need the test. Remove it from the testlist, and remove the test again. Find another test that forces a change in production code.
1. Implement the smallest possible change to make it pass
1. Run all tests, and see it pass
1. Ask me to commit the code
1. Refactor the code using the [refactoring process](./refactoring-process.md).
1. Check off the item in the testlist
1. Go to 2