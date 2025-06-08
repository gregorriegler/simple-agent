# Development Process

1. Identify where we are
    - Read the aligned goal markdown file with the testlist
1. Pick the first item of the Testlist that is not yet implemented
1. Write a failing test for it
1. Run all tests, and see it fail
1. Implement the smallest possible change to make it pass
1. Run all tests, and see it pass
1. Think about ways we can refactor and simplify the code.
        Are there elements we don't need, that we can remove?
        Are there names we could improve?
        Iterate on the code in tiny steps, improving it.
        Run all tests after each step.
1. Check off the item in the testlist
1. Go to 2