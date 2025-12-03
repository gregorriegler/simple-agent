# Answering Rules
ALWAYS start your answers with a STARTER_SYMBOL
The default STARTER_SYMBOL is 🐙
You can omit the STARTER_SYMBOL on Tool Call Messages

We prefer very short and succinct answers.
We prefer an empirical approach to problem solving.
Whenever we are tackling a problem we first create a hypothesis and then try to prove it.
Add a Confidence Indicator telling your confidence on a range from 1 to 10, where 1 means not confident at all and 10 means absolutely confident, when concluding 
Example: 
The problem is that there is a missing semicolon. Confidence: [10/10]
The problem is that ... [3/10]

## Architecture
- We are following a minimal ports and adapters architecture which means there is main, application and infrastructure where
  - main depends on both application and infrastructure,
  - infrastructure depends on application,
  - and application may never depend on the other two.
  - whenever application needs access to infrastructure we implement a port and an adapter 
  - whenever we unittest we cover what is in application
  - infrastructure is tested only by integration tests

# Environment
- We are in a bash environment
- We use uv
- To run the tests use the `./test.sh` script
  - `./test.sh` - Run all tests (stops on first failure, short tracebacks)
  - `./test.sh test_foo.py` - Run a specific test file
  - `./test.sh test_foo` - Run tests matching a pattern
  - `./test.sh -v` - Verbose mode with full tracebacks
  - `./test.sh -h` - Show help
- avoid interactive commands such as `git diff`.
  - E.g. use `git --no-pager diff` instead
