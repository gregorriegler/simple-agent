# Self-Closing Tool Syntax

## Problem

The current tool call syntax allows tools that have only a header (no body):

```
🛠️[ls dir]
```

But the parser doesn'\''t know whether a `🛠️[/end]` is coming or not. It has to use heuristics like "is there only whitespace until the next tool or end of string?" This is ambiguous, especially during streaming.

## Solution

Introduce explicit self-closing syntax for header-only tool calls:

- **Header-only (self-closing):** `🛠️[tool args /]`
- **With body:** `🛠️[tool args]` ... `🛠️[/end]`

### Rules

1. A space is required before ` /]` to avoid ambiguity with paths (e.g., `ls /home/user /]` not `ls /home/user/]`)
2. Tools with a body continue to use `🛠️[/end]` 
3. No backwards compatibility - all header-only tools must use ` /]`

### Examples

Header-only tools:

```
🛠️[ls /home/user /]
🛠️[cat file.txt /]
🛠️[bash echo hello /]
```

Tools with body:

```
🛠️[create-file script.py]
print("he