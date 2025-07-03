# Write a Failing Test

STARTER_SYMBOL = 🔴

Your answers should be succinct and concise.

1. Identify where you are

    * Read the `README.md` to understand your current context.
    * Read the `goal.md` to understand your next goal, scenarios, and examples.
    * Run `pwd` to verify the current working directory.

2. Ensure there are no uncommitted changes

    * **STOP** immediately if uncommitted changes are detected.

3. Confirm all current tests pass by executing `./test.sh`

    * Proceed only if all tests pass successfully.

4. Select the next example to implement

    * Choose the first example that has not yet been implemented.
    * If no examples remain in the current refined scenario, begin a new context using the prompt: "Read and follow the `process/refine-scenarios.md` instructions."

5. Write a failing test

    * The test should be the simplest possible test that demonstrates the required change.
    * Writing a failing test is **ALWAYS** the initial step when changing production code.
    * The test must use domain-specific language and avoid implementation details.

6. Hypothesize the test outcome

    * Clearly state your expectation: Will the test fail? Why?

7. Run the test using `./test.sh` and observe the outcome

    * **Note**: Verify or ApprovalTests will fail initially because they require approval.
    * If the `received.txt` content matches your expectations, approve it using: `./approve.sh name_of_the_test`
    * After approval, consider it a **PASSING** test and commit using: "t <message>"

8. Handle passing tests

    * If the test passes immediately, no changes to the production code are necessary.
    * Initiate the next context using the prompt: "Read `process/write-a-failing-test.md` and follow the process."
