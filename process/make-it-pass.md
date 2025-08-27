# Make the failing test pass

STARTER_SYMBOL=🟢

1. To understand where we are read the `README.md` and `goal.md`.
2. Run the test using `./test.sh`. There should be exactly one failing test. If there are more failing tests STOP. If there is no failing test end this task with the message "No failing test found".
3. Think, Is there a design different from the current one, that would make passing the tests easier? 
  - If yes, create a new SubTask with the prompt: "Read `process/preparatory-refactoring.md and follow it. We're working on making the test <test-name> pass. <Description-how-we-would-make-it-pass>. But first, we need the following design improvement, to make that easier: <Desired-design-improvement>."
  - If no, just continue and make the test pass.
4. Make the smallest possible change to make the failing test and all other tests pass
5. If the tests unexpectedly don't pass after your changes create a new SubTask with the prompt "read and follow `process/debug.md`"
6. Make sure the system has at least a walking skeleton for the feature we are building in place. If that's not the case, create the walking skeleton now.
7. Run the tests, and see it pass
8. Check off the item in the examples in `goal.md`
9. Commit the code. Prefix the commit message with "f", e.g. "f can rename methods"
10. End the task with the message "Made the test pass"
