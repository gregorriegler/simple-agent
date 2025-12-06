# Centralize Tool Parsing Specification

## Problem Statement

Tool examples are currently hardcoded as syntax strings in ~12 tool implementation files. When the tool call syntax needs to change (e.g., from `🛠️` emoji format to XML tags), each example must be manually updated.

Example from `bash_tool.py`:
```python
examples = [
    "🛠️ bash echo hello",
    "🛠️ bash ls -la",
    "🛠️ bash pwd"
]
```

**The core problem:** Manual maintenance burden when changing syntax format.
- ~12 tool files with hardcoded examples
- Additional test fixtures with hardcoded syntax
- Each syntax change requires manual string updates across all files
- Error-prone and time-consuming

## Solution Summary

**Core Idea:** Decouple tool examples from syntax by using structured data and argument metadata.

**Approach:**
1. **Enhanced `Argument` metadata** - Add `multiline` flag to indicate formatting requirements
2. **Structured examples** - Store as dicts (`{"command": "echo hello"}`) instead of strings (`"🛠️ bash echo hello"`)
3. **Phased rollout** - First tool examples, then test fixtures

**Result:** Examples become pure data, decoupled from syntax format. When syntax changes later, examples adapt automatically through formatting logic (to be implemented in a future phase).

## Current Architecture

### Centralized Components ✅

#### 1. Tool Call Parsing
**File:** `simple_agent/application/tool_message_parser.py`

The `parse_tool_calls()` function is the single place where tool calls from LLM responses are parsed.

```python
def parse_tool_calls(text: str) -> ParsedMessage:
    pattern = r'^🛠️ ([\w-]+)(?:\s+(.*))?'  # Line 18
    end_marker = r'^🛠️🔚'                    # Line 19
```

**Key characteristics:**
- Parses lines starting with 🛠️ followed by tool name and optional arguments
- Supports multi-line arguments until end marker 🛠️🔚 or next tool
- Returns `ParsedMessage(message, tool_calls)`

#### 2. Tool Library Interface
**File:** `simple_agent/application/tool_library.py`

Defines the protocol/interface:
- `ToolLibrary.parse_message_and_tools()` - delegates to parser
- `Tool.get_usage_info()` - protocol method for tool documentation
- `Tool.execute()` - protocol method for tool execution

#### 3. Tool Documentation Generation Infrastructure

**File:** `simple_agent/application/tool_documentation.py`

The `generate_tools_documentation()` function:
- Calls `tool.get_usage_info()` on each tool
- Formats tool documentation for system prompts
- Header says "To use a tool, answer in the described syntax" (Line 7-9)

**File:** `simple_agent/tools/base_tool.py`

The `_generate_usage_info_from_metadata()` method:
- Line 79: Generates `syntax = f"🛠️ {self.name}"`
- Line 82: Adds to documentation as `Usage: {syntax}`
- Automatically builds documentation from tool metadata (name, description, arguments)

### Decentralized Components ⚠️

#### 1. Tool Examples (Hardcoded)

Every tool class has an `examples` list that hardcodes the 🛠️ emoji syntax:

**`simple_agent/tools/bash_tool.py:16-20`**
```python
examples = [
    "🛠️ bash echo hello",
    "🛠️ bash ls -la",
    "🛠️ bash pwd"
]
```

**`simple_agent/tools/cat_tool.py:23-26`**
```python
examples = [
    "🛠️ cat myfile.txt",
    "🛠️ cat script.py 1-20"
]
```

**`simple_agent/tools/create_file_tool.py:30-34`**
```python
examples = [
    "🛠️ create-file newfile.txt",
    "🛠️ create-file script.py\nprint(\"Hello World\")🛠️🔚",
    "🛠️ create-file multi-line.py\nLine 1\nLine 2\n🛠️🔚",
]
```

**`simple_agent/tools/subagent_tool.py:24-27`**
```python
examples = [
    "🛠️ subagent default Write a Python function to calculate fibonacci numbers",
    "🛠️ subagent default Create a simple HTML page with a form"
]
```

**Other tools with hardcoded examples:**
- `simple_agent/tools/write_todos_tool.py`
- `simple_agent/tools/edit_file_tool.py`
- `simple_agent/tools/complete_task_tool.py`
- `simple_agent/tools/ls_tool.py`
- `simple_agent/tools/remember_tool.py`
- `simple_agent/tools/patch_file_tool.py`
- `simple_agent/tools/recall_tool.py`

**Total: ~12 tool files with hardcoded examples**

#### 2. Test Fixtures

**`simple_agent/application/llm_stub.py:35-46`**

Test stubs hardcode complete tool call responses:
```python
[
    "Starting task\n🛠️ subagent orchestrator Run bash echo hello world and then complete",
    "Subagent1 handling the orchestrator task\n🛠️ subagent coding Run bash echo hello world and then complete",
    "Subagent2 updating todos\n🛠️ write-todos\n- [x] Feature exploration\n- [ ] **Implementing tool**\n- [ ] Initial setup\n🛠️🔚",
    "Subagent2 running the bash command\n🛠️ bash echo hello world",
    # ... more examples
]
```

#### 3. Test Files with Hardcoded Syntax

**`tests/application/tool_message_parser_test.py`**
- Contains test cases with hardcoded 🛠️ syntax for parser validation

**`tests/agent/agent_test.py`**
- Test responses contain hardcoded tool calls

**`tests/agent/subagent_test.py`**
- Test responses contain hardcoded tool calls

## Impact Analysis: What Needs to Change

To change the tool call syntax from the current 🛠️-based format to a new format:

### Must Change (Core Logic)
1. ✅ `tool_message_parser.py:18-19` - Update regex patterns (1 location)
2. ✅ `base_tool.py:79` - Update usage line generation (1 location)
3. ✅ `tool_documentation.py:7-9` - Update header instructions (1 location)

### Must Change (Examples)
4. ⚠️ All tool `examples` arrays in ~12 tool files
5. ⚠️ `llm_stub.py` test fixture responses
6. ⚠️ Test files with hardcoded tool calls

### Total Estimated Changes: ~15-20 locations

**Note:** Approved test files will be automatically regenerated and are not a concern.

## Proposed Solution

### Phase 1: Enhanced Argument Metadata

Extend the `Argument` dataclass to include formatting hints:

**File:** `simple_agent/tools/base_tool.py` (or wherever `Argument` is defined)

```python
@dataclass
class Argument:
    """Metadata for a tool argument."""
    name: str
    description: str
    required: bool = True
    multiline: bool = False  # NEW: Indicates if argument expects multi-line content
```

**Purpose:** The `multiline` flag provides metadata about how arguments should be formatted:
- `multiline=False` (default): Argument appears on same line as tool name
- `multiline=True`: Argument content appears on separate lines with end marker

This metadata will enable future formatting logic to automatically generate examples in any syntax format.

### Phase 2: Convert Tool Examples to Structured Data

Transform tool examples from hardcoded syntax strings to structured dicts.

#### Phase 2.1: Tool Implementation Files (~12 files)

**Example: Simple tool (bash)**

Before:
```python
class BashTool(BaseTool):
    name = 'bash'

    examples = [
        "🛠️ bash echo hello",
        "🛠️ bash ls -la",
        "🛠️ bash pwd"
    ]
```

After:
```python
class BashTool(BaseTool):
    name = 'bash'

    arguments = [
        Argument(name="command", description="Shell command to execute", required=True)
    ]

    examples = [
        {"command": "echo hello"},
        {"command": "ls -la"},
        {"command": "pwd"}
    ]
```

**Example: Multi-line tool (create-file)**

Before:
```python
class CreateFileTool(BaseTool):
    name = 'create-file'

    examples = [
        "🛠️ create-file newfile.txt",
        "🛠️ create-file script.py\nprint(\"Hello World\")🛠️🔚",
    ]
```

After:
```python
class CreateFileTool(BaseTool):
    name = 'create-file'

    arguments = [
        Argument(name="file_path", description="Path to the file", required=True),
        Argument(name="content", description="File content", required=False, multiline=True)
    ]

    examples = [
        {"file_path": "newfile.txt", "content": ""},
        {"file_path": "script.py", "content": "print(\"Hello World\")"},
    ]
```

#### Phase 2.2: Test Fixtures (`llm_stub.py`)

Convert test fixture responses from hardcoded strings to structured format.

**Details:** To be determined during implementation - may keep as strings or convert to dict-based generation.

### Implementation Steps

1. ✅ Add `multiline` field to `Argument` dataclass
2. ✅ Update all ~12 tool implementations:
   - Add/update `arguments` list with metadata (including `multiline` flags)
   - Convert `examples` from string arrays to dict arrays
3. ✅ Update `llm_stub.py` test fixtures (approach TBD)
4. ✅ Verify all tests pass
5. ✅ Update any tool-related documentation

## Benefits

After Phase 1 & 2 implementation:
- **Decoupled examples** - Tool examples are pure data (dicts), not syntax strings
- **Reduced maintenance** - No manual string updates needed when syntax changes
- **Self-documenting** - Argument metadata with `multiline` flag makes formatting intent explicit
- **Declarative** - Examples describe "what" (data), not "how" (syntax)
- **Validatable** - Can verify example keys match defined arguments at runtime/test time
- **Foundation for future** - Enables automatic formatting logic in future phases

## Future Work

This phase focuses on decoupling data from syntax. Future phases will add:
- Automatic formatting logic that uses argument metadata to generate syntax strings
- ToolSyntax class for centralized syntax configuration
- Support for multiple syntax formats (emoji, XML, brackets, etc.)

## Before/After Comparison

### Example 1: Simple Tool (Bash)

**Before:**
```python
class BashTool(BaseTool):
    name = 'bash'

    examples = [
        "🛠️ bash echo hello",
        "🛠️ bash ls -la",
        "🛠️ bash pwd"
    ]
```

**After:**
```python
class BashTool(BaseTool):
    name = 'bash'

    arguments = [
        Argument(name="command", description="Shell command to execute", required=True)
    ]

    examples = [
        {"command": "echo hello"},
        {"command": "ls -la"},
        {"command": "pwd"}
    ]
```

**Key changes:**
- Added `arguments` metadata
- Converted `examples` from syntax strings to data dicts
- Examples now describe arguments, not syntax

### Example 2: Multi-line Tool (CreateFile)

**Before:**
```python
class CreateFileTool(BaseTool):
    name = 'create-file'

    examples = [
        "🛠️ create-file newfile.txt",
        "🛠️ create-file script.py\nprint(\"Hello World\")🛠️🔚",
    ]
```

**After:**
```python
class CreateFileTool(BaseTool):
    name = 'create-file'

    arguments = [
        Argument(name="file_path", description="Path to the file", required=True),
        Argument(name="content", description="File content", required=False, multiline=True)
    ]

    examples = [
        {"file_path": "newfile.txt", "content": ""},
        {"file_path": "script.py", "content": "print(\"Hello World\")"},
    ]
```

**Key changes:**
- Added `arguments` metadata with `multiline=True` for content
- Converted `examples` to dicts
- No more hardcoded `🛠️` or `🛠️🔚` markers in examples

## Related Files Reference

### Core Files
- `simple_agent/application/tool_message_parser.py` - Parsing logic
- `simple_agent/application/tool_library.py` - Tool protocol
- `simple_agent/application/tool_documentation.py` - Documentation generation
- `simple_agent/tools/base_tool.py` - Base tool implementation
- `simple_agent/tools/all_tools.py` - Tool registry

### Tool Implementations (All need update)
- `simple_agent/tools/bash_tool.py`
- `simple_agent/tools/cat_tool.py`
- `simple_agent/tools/create_file_tool.py`
- `simple_agent/tools/edit_file_tool.py`
- `simple_agent/tools/complete_task_tool.py`
- `simple_agent/tools/ls_tool.py`
- `simple_agent/tools/subagent_tool.py`
- `simple_agent/tools/write_todos_tool.py`
- `simple_agent/tools/remember_tool.py`
- `simple_agent/tools/patch_file_tool.py`
- `simple_agent/tools/recall_tool.py`

### Test Infrastructure
- `simple_agent/application/llm_stub.py` - Test fixtures
- `tests/application/tool_message_parser_test.py` - Parser tests
- `tests/agent/agent_test.py` - Agent integration tests
- `tests/agent/subagent_test.py` - Subagent tests
