# Write a Failing Test

STARTER_SYMBOL = 🔴

Your answers should be succinct and concise.

1. Understand where you are
    - Read the `README.md` and `goal.md`.
    - Run `pwd`.
2. Ensure there are no uncommitted changes
    - **STOP** immediately if uncommitted changes are detected.
3. Confirm all current tests pass by executing `./test.sh`
    - Proceed only if all tests pass successfully.
4. Select the next example to implement
    - Choose the first example that has not yet been implemented.
    - If no examples remain in the current refined scenario, begin a new context using the prompt: "Read and follow the `process/refine-scenarios.md` instructions."
5. Think: Will this already work given the current implementation? And is there already testcode forcing this behavior?
6. If the answer is yes to both, check off the item in `goal.md` and proceed with 3. 
6. Otherwise, write a failing test
    - The test should be the simplest possible test that demonstrates the required change.
    - Writing a failing test is **ALWAYS** the initial step when changing production code.
    - The test must use domain-specific language and avoid implementation details.
6. Hypothesize the test outcome
    - Clearly state your expectation: Will the test fail? Why?
7. Run the test using `./test.sh` and observe the outcome
    - **Note**: Verify or ApprovalTests will fail initially because they require approval.
8. If it was an approval or Verify test and the `received.txt` content matches your expectations, approve it using: `./approve.sh name_of_the_test`
9. Commit if passes. If all the tests pass now commit using the message: "t <message>"
10. If the tests fail, STOP and END there.
11. Initiate the next context using the prompt: "Read `process/write-a-failing-test.md` and follow the process."
