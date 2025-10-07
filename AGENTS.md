# Answering Rules
ALWAYS start your answers with a STARTER_SYMBOL
The default STARTER_SYMBOL is 🐙
You can omit the STARTER_SYMBOL on Tool Call Messages

ALWAYS give SHORT and SUCCINCT answers

ALWAYS Add a Confidence Indicator telling your confidence on a range from 1 to 10, where 1 means not confident at all and 10 means absolutely confident, when concluding 
Example: 
The problem is that there is a missing semicolon. Confidence: [10/10]
The problem is that ... [3/10]

Prefer empirical problem solving.
First create a hypothesis and prove it.
Do not assume that I (the user) am always right.

# Coding Rules
- NEVER ADD COMMENTS
- If I tell you to change the code, do the following first:
  1. Run `./test.sh`, we do not start with failing tests
- AFTER EACH STEP: run `./test.sh` again
- As we read from top to bottom, called functions should be below their calling functions
- Avoid else if possible
- Avoid overly defensive programming and focus on the happy path first

# Python specific
- We use uv

## Design rules
- We are following a minimal ports and adapters architecture which means there is main, application and infrastructure where
  - main depends on both application and infrastructure,
  - infrastructure depends on application,
  - and application may never depend on the other two.
  - whenever application needs access to infrastructure we implement a port and an adapter 
  - whenever we unittest we work with application
  - infrastructure is tested only via integration tests
- Each class goes into its own file, unless its only used by the other class in the same file and it both fits into 100 lines
- declare a variable as late as possible and as close as possible to where it is used, except imports
- When a function uses only a derived, or a small percentage of properties of a passed object, pass the specific elements instead.
- CQS (command and query separation): a function should either just calculate and return something thus be a query, or be void, but therefore have a side effect, but never both.
  - We do not create commands that return a boolean to control flow. The ONLY EXCEPTION where we may return a boolean is a query.

## Specific to Test Code
- A testname specifies what the application does without going into too much detail. The name describes a fact. The name should not contain can/should/handle in its name.
- Separate Arrange, Act and Assert by one line of whitespace
- NEVER use a block syntax structure such as Loops or ifs in a test. The test has only one path and it knows the expected outcome. References list contents directly or uses prebuilt Collection Asserts.
- Test readability trumps code reuse!
  - Keep test data inline when the data structure IS what's being tested.

# Commandline rules
- We are in Bash, so USE BASH
- for interacting with github use the github cli
- avoid interactive commands such as `git diff`.
  - E.g. use `git --no-pager diff` instead

# Commit rules
We use Arlos commit notation V1
Risk-based prefixes (lowercase = safe, uppercase = risky):

f/F - Feature (small/large)
b/B - Bug fix (small/large)
r/R/R!! - Refactor (safe/risky/dangerous)
t - Test (always safe)
d - Documentation (no code change)

Example: r rename userId to id in User class

