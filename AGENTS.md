# Answering Rules
Start your answers with a STARTER_SYMBOL
The default STARTER_SYMBOL is 🐙
You can omit the STARTER_SYMBOL on Tool Call Messages

When you're not confident that you completely understood the users request, please ask clarifying questions.
Provide short and succinct answers.

Add a Confidence Indicator telling your confidence on a range from 1 to 10, where 1 means not confident at all and 10 means absolutely confident, when concluding 
Example: 
The problem is that there is a missing semicolon. Confidence: [10/10]
The problem is that ... [3/10]

# Architecture
To get an overview of the Architecture read `docs/overview.md`

# Software Engineering 
Apply empirical problem-solving and first come up with an hypothesis to then try and prove it. When adding a new feature, a test can serve as a hypothesis that the feature doesn't exist yet. When fixing a bug, write a test as an hypothesis to indicate the problem.
In this project we apply strict Test Driven Development.

# Environment
- This is a bash environment, using uv.
- For testing use pytest.
- Avoid excessive code comments.
- Always us the `./test.sh` script to run the tests
  - `./test.sh` - Runs all tests
  - `./test.sh test_foo.py` - Run a specific test file
  - `./test.sh test_foo` - Run tests matching a pattern
  - `./test.sh -v` - Verbose mode with full tracebacks
  - `./test.sh -h` - Show help

- avoid interactive commands such as `git diff`.
  - E.g., use `git --no-pager diff` instead
 
# Commit rules
This project uses Arlos commit notation V1
Risk-based prefixes (lowercase = safe, uppercase = risky):

f/F - Feature (small/large)
b/B - Bug fix (small/large)
r/R/R!! - Refactor (safe/risky/dangerous)
t - Test (always safe)
d - Documentation (no code change)
e - Environment

Example:
r extract slash command handler
