# Make the failing test pass

STARTER_SYMBOL=🟢

1. Understand where we are
    - Read the `README.md` and `goal.md`.
    - Run `pwd`.
2. Run the test using `./test.sh`. There should be exactly one failing test. If there are more failing tests STOP. If there is no failing test continue with another SubTask with the prompt: "Read `process/write-a-failing-test.md` and follow the process."
3. Make sure the system has at least a walking skeleton for the feature we are building in place. If that's not the case, create the walking skeleton now.
4. Implement the smallest possible change to make the failing test and all other tests pass
5. Run the tests, and see it pass
6. Check off the item in the examples in `goal.md`
7. Commit the code. Prefix the commit message with "f", e.g. "f can rename methods"
8. End this process by creating a new context with the prompt "Refactor the code using the [refactoring process](./process/refactor.md)"
