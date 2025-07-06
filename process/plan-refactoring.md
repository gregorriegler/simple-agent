## Plan a refactoring

STARTER_SYMBOL=📝

1. If there is already a `refactoring-plan.md` file, clean it so it's empty.
2. Identify one thing to improve
3. Find one thing to improve. E.g.:
    - Remove Comments
    - Remove Dead code
    - Remove production code that is not exercised by any tests. If you are unsure whether you can remove production code, run a [mutation test](./mutation-test.md)
    - Fix Feature Envy
    - Make duplicated code visible by rearranging the code so the duplication is obvious 
    - Extract duplicated code
    - Refactor Long Methods
    - Long Parameter Lists (more than 3 is long)
    - Long Classes
    - Long Files
    - Improve Names
4. Think, whether the thing you want to improve can be decomposed into small steps that leave the tests passing.
5. List all the steps as tasks prefixed with a checkbox in `refactoring-plan.md`.
