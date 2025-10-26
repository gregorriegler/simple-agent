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
First create a hypothesis and then prove it.

# Python specific
- We use uv

## Architecture
- We are following a minimal ports and adapters architecture which means there is main, application and infrastructure where
  - main depends on both application and infrastructure,
  - infrastructure depends on application,
  - and application may never depend on the other two.
  - whenever application needs access to infrastructure we implement a port and an adapter 
  - whenever we unittest we work with application
  - infrastructure is tested only via integration tests

# Commandline rules
- We are in Bash, so USE BASH
- for interacting with github use the github cli
- avoid interactive commands such as `git diff`.
  - E.g. use `git --no-pager diff` instead
