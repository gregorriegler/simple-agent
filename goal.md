# Goal: Fix System Prompt Generator Argument Handling

## Problem
The `modernizer/system_prompt_generator.py` file does not provide proper info about arguments when run directly. It lacks command-line interface and argument parsing.

## Testlist
- [x] System prompt generator should show help when run with --help
- [x] System prompt generator should generate system prompt to stdout when run without arguments
- [x] System prompt generator should handle invalid arguments gracefully
- [x] Create a helper program that generates the system prompt to stdout
- [x] System prompt generator should show specific arguments instead of generic <arguments>
- [x] Document CodeSelection and Cursor formats with examples in the system prompt