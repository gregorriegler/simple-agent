
# Emoji-Bracket Tool Call Syntax Specification (v1)

This document specifies a compact, emoji-based syntax for representing tool calls in LLM output.

The syntax is designed to be:
- **Token-efficient** (short markers, minimal boilerplate)
- **Easy for models to follow** (simple, repeated pattern)
- **Easy to parse** (unambiguous delimiters)
- **Line-break agnostic** (works even if tools do not start at the beginning of a line)

---

## 1. Basic Structure

A tool call is a **block** with:

- A **start marker** containing a header:
  ```text
  🛠️[<header>]
  ```
- An optional **body** (any text, including newlines)
- A mandatory **end marker**:
  ```text
  🛠️[/end]
  ```

Visually:

```text
🛠️[<header>]
<body>
🛠️[/end]
```

Tool blocks can appear **anywhere** in the LLM output (not necessarily at the start of a line), and you can have **multiple blocks** in a single response.

---

## 2. Header Format

The header is a single line of text between `🛠️[` and `]`.

### 2.1. Required parts

- **Tool name**: first token (no spaces)
- **Argument string**: the rest of the header (optional, free-form)

Example:

```text
🛠️[create-file script.py]
```

Here:

- Tool name: `create-file`
- Argument string: `script.py`

Another example:

```text
🛠️[run-query main.sql 100]
```

- Tool name: `run-query`
- Argument string: `main.sql 100`

### 2.2. Tool name rules

Tool names SHOULD:

- Use only: `a–z`, `A–Z`, `0–9`, `_`, `-`
- Start with a letter (recommended)

Examples of valid tool names:

- `create-file`
- `run_query`
- `tool1`
- `generate-report`

### 2.3. Arguments

The argument string allows for positional arguments

- **Positional arguments**:
  ```text
  🛠️[create-file script.py utf-8]
  ```

---

## 3. Body

The **body** is the content between the header line and the end marker:

```text
🛠️[create-file script.py]
print("Hello World")
🛠️[/end]
```

Rules:

- The body MAY be empty.
- The body MAY contain arbitrary text, including:
  - Newlines
  - Markdown
  - Code blocks
  - Other non-tool content
- The body MUST NOT contain the exact substring `🛠️[/end]` unless it is intended to terminate the block. If this is possible (e.g., user input), it should be escaped or otherwise encoded by the system before sending to the model.

---

## 4. End Marker

The end marker is always:

```text
🛠️[/end]
```

Requirements:

- MUST be written exactly as above (no extra header or arguments).
- Terminates the **nearest preceding unclosed** tool block.

Example with two sequential blocks:

```text
🛠️[create-file script.py]
print("Hello World")
🛠️[/end]

🛠️[create-file readme.md]
# Hello
This is a README.
🛠️[/end]
```

---

## 5. Parsing Specification

Given an arbitrary string `S` (LLM output), a parser should extract tool calls as follows.

### 5.1. High-level algorithm (conceptual)

1. Search for the substring `🛠️[`.
2. From that index, find the next `]`.
   - The text between `🛠️[` and `]` is the **header**.
3. From the character **after** this `]`, find the next occurrence of `🛠️[/end]`.
   - All text between them is the **body**.
4. Emit a tool call:
   - `tool_name`: first whitespace-separated token from header
   - `raw_args`: the rest of the header string (may be empty)
   - `body`: the extracted body
5. Continue scanning after the `🛠️[/end]` marker to find additional tool calls.

### 5.2. Formal-ish grammar (EBNF-style)

```ebnf
text               = { char } ;

tool_block         = start_marker header_close body end_marker ;

start_marker       = "🛠️[" ;
header_close       = "]" ;
end_marker         = "🛠️[/end]" ;

header             = tool_name , [ " " , arg_string ] ;
tool_name          = letter , { letter | digit | "_" | "-" } ;
arg_string         = { char - newline - "]" } ;

body               = { char } ;  (* up to but not including end_marker *)

letter             = "A" | ... | "Z" | "a" | ... | "z" ;
digit              = "0" | ... | "9" ;
newline            = "\n" ;
char               = any Unicode character ;
```

Notes:

- The parser SHOULD be robust to surrounding text and multiple tool blocks.
- The parser MUST NOT assume tool blocks are line-aligned.

### 5.3. Example parser behavior

Given:

```text
Here is your file:
🛠️[create-file script.py]
print("Hello World")
🛠️[/end]
Hope that helps!
```

The parser should extract **one** tool call with:

- `tool_name`: `create-file`
- `raw_args`: `script.py`
- `body`: `print("Hello World")\n`

The rest of the text ("Here is your file:", "Hope that helps!") is normal assistant text.

---

## 6. Multiple Tool Calls

Multiple tool calls can appear in a single response, either adjacent or interleaved with natural language.

Example:

```text
I will create two files for you.

🛠️[create-file main.py]
print("Hello from main")
🛠️[/end]

🛠️[create-file utils.py]
def helper():
    return "helper"
🛠️[/end]

Both files have been defined.
```

The parser should extract two independent tool blocks in order of appearance.

---

## 7. Error Handling Guidelines

An implementation MAY apply the following behaviors when encountering malformed blocks.

### 7.1. Missing closing `]` in header

If `🛠️[` is found but no closing `]` exists afterward, the parser SHOULD:

- Treat it as plain text (no tool call), and
- Continue scanning after that position.

### 7.2. Missing `🛠️[/end]`

If a header is found and parsed, but no matching `🛠️[/end]` appears afterward, the parser MAY:

- Treat the rest of the string as the body (best effort)

### 7.3. Invalid tool name

If the first token of the header does not match the `tool_name` rules, the parser:

- Treat `tool_name` as-is (lenient mode) and pass it to a higher-level dispatcher which may reject it.

### 7.4. Nested or overlapping blocks

Nested blocks are **not supported** in v1 of this specification. If the body contains another `🛠️[` before `🛠️[/end]`, the parser SHOULD:

- Treat the inner `🛠️[` as plain text
