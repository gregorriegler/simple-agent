# Answering Rules
Start your answers with a STARTER_SYMBOL
The default STARTER_SYMBOL is 🐙
You can omit the STARTER_SYMBOL on Tool Call Messages

When you're not confident that you completely understood a user request, please ask clarifying questions.
Prefer very short and succinct answers.
Apply empirical problem-solving and first come up with an hypothesis and then try to prove it.

Add a Confidence Indicator telling your confidence on a range from 1 to 10, where 1 means not confident at all and 10 means absolutely confident, when concluding 
Example: 
The problem is that there is a missing semicolon. Confidence: [10/10]
The problem is that ... [3/10]

# Architecture
To get an overview of the Architecture read `doc/overview.md`

# Environment
- You are in a bash environment, using uv
- To run the tests use the `./test.sh` script
  - `./test.sh` - Run all tests (stops on first failure, short tracebacks)
  - `./test.sh test_foo.py` - Run a specific test file
  - `./test.sh test_foo` - Run tests matching a pattern
  - `./test.sh -v` - Verbose mode with full tracebacks
  - `./test.sh -h` - Show help
- avoid interactive commands such as `git diff`.
  - E.g., use `git --no-pager diff` instead
