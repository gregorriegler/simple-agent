# Perform a preparatory refactoring leading to a desired design improvement

STARTER_SYMBOL=✨

Inputs: 
- The test we would like to make pass.
- How we would like to make it pass.
- The desired design improvement that would make it easier to make the test pass.

1. Run the tests using ./test.sh, we expect just one of them to fail - the one we would like to make pass
2. Disable the test,
3. Run the tests, they should now pass.
4. commit with the message "t <message>"
5. Make the desired design improvement/preparatory refactoring.
6. Run the tests, they should still pass.
7. git commit with the message "r preparatory: <message>".
8. End this context with a summary.
