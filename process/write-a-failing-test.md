# Write a Failing Test

STARTER_SYMBOL = 🔴

1. To understand where you are read `README.md` and `goal.md`.
2. Ensure there are no uncommitted changes
    - **STOP** immediately if uncommitted changes are detected. use `./say.py` to notify me
3. Confirm all current tests pass by executing `./test.sh`
    - Proceed only if all tests pass. If they don't stop and notify me using `./say.py`
4. Before picking the next example in the goal, analyze the recently changed production code and search for hardcoded, faked and incomplete implementation that needs proper implementation. If you can find one, come up with a minimum example that would drive that implementation or a part of it. Insert this example into the `goal.md` before the next example, if not already given.
5. Pick the next example in `goal.md`
6. Think: Will this example already work given the current production code? Do we already have testcode forcing this behavior?
7. If the answer two both is yes, then we don't have to add any code. Check off the item in `goal.md` and proceed with 3. 
8. Otherwise, write a failing test
    - It should be the simplest possible test that demonstrates that the feature does not yet exist.
    - The test must use domain-specific language and avoid talking implementation details.
9. Hypothesize the test outcome
    - Clearly state your expectation: Will the test fail? Why?
10. Run the test using `./test.sh` and observe the outcome
    - **Note**: Verify or ApprovalTests will fail initially because they require approval.
11. If it surprisingly already passes, or the received.txt is already what it should be, we approve it using `./approve.sh`. We then commit with the message "t ..."
12. Only if we have a failing test to make pass, end this task with the message: "Added a failing Test"
13. Otherwise commit with the message "t ..." and continue from 2.
