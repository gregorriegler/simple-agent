# Tool Syntax Abstraction Specification

## Problem Statement

After implementing `ToolArgument` metadata and converting tool examples to structured data (commit ebb268e), we achieved ~70% decoupling of tools from syntax. However, **formatting logic still hardcodes the tool call syntax** in multiple locations:

### Current Issues

1. **Syntax hardcoded in formatting logic:**
   - `simple_agent/tools/base_tool.py:106` - `syntax = f"🛠️ {self.name}"`
   - `simple_agent/tools/base_tool.py:114-118` - `syntax += "🛠️🔚"`
   - `simple_agent/tools/base_tool.py:144` - `syntax = f"🛠️ {self.name}"`

2. **Syntax hardcoded in parsing logic:**
   - `simple_agent/application/tool_message_parser.py:18` - `pattern = r'^🛠️ ([\w-]+)(?:\s+(.*))?'`
   - `simple_agent/application/tool_message_parser.py:19` - `end_marker = r'^🛠️🔚'`

3. **Syntax hardcoded in display logic:**
   - `simple_agent/application/tool_library.py:40` - `return f"🛠️ {self.name} {self.arguments}"`

4. **Mixed concerns in Tool protocol:**
   - `Tool.get_usage_info()` mixes data representation with formatting
   - Tool protocol is not pure data - it has formatting responsibilities

### Impact

To change from `🛠️` syntax to another Syntax (whatever that syntax might be):
- Must update 5 locations across 3 files
- Tool protocol conflates data with presentation
- Cannot easily support multiple syntaxes or syntax switching

## Proposed Solution: ToolSyntax Abstraction

### Core Principle

**Separate data from presentation:**
- **Tool** = Pure data interface (name, arguments, examples)
- **ToolSyntax** = Formatting and parsing logic
- Tool never references ToolSyntax (one-way dependency)

### Design

```
┌─────────────────────────────────────┐
│ Tool (Protocol)                     │
│ Pure data interface                 │
│ - name, description, arguments      │
│ - examples, execute()               │
│ NO formatting logic                 │
└─────────────────────────────────────┘
                ↑
                │ knows about
                │
┌─────────────────────────────────────┐
│ ToolSyntax (Protocol)               │
│ Formatting & parsing logic          │
│ - render_documentation(tool)        │
│ - parse(text)                       │
└─────────────────────────────────────┘
                ↑
                │ uses
                │
┌─────────────────────────────────────┐
│ Documentation & Parsing Code        │
│ - tool_documentation.py             │
│ - tool_message_parser.py            │
└─────────────────────────────────────┘
```

## Component Specifications

### 1. Tool Protocol (Pure Data)

**File:** `simple_agent/application/tool_library.py`

**Responsibilities:**
- Define data interface for tools
- Provide execution contract
- Allow documentation customization (finalize_documentation)
- **NO formatting or syntax logic**

**Interface:**
```python
class Tool(Protocol):
    """Pure data interface for tools."""

    @property
    def name(self) -> str:
        """Tool identifier (e.g., 'bash', 'cat')."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        ...

    @property
    def arguments(self) -> List[ToolArgument]:
        """Argument definitions with metadata (name, type, required, multiline)."""
        ...

    @property
    def examples(self) -> List[Dict[str, Any]]:
        """Example invocations as structured data (not syntax strings)."""
        ...

    def execute(self, *args, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        ...

    def finalize_documentation(self, doc: str, context: dict) -> str:
        """Customize generated documentation (e.g., substitute {{PLACEHOLDERS}})."""
        ...
```

**Changes from current:**
- **REMOVE** `get_usage_info()` method (formatting concern, not data)
- **ADD** properties: `description`, `arguments`, `examples`

### 2. ToolSyntax Protocol (Formatting & Parsing)

**File:** `simple_agent/application/tool_syntax.py` (NEW)

**Responsibilities:**
- Format tool calls for documentation and display
- Parse text to extract tool calls
- Encapsulate ALL syntax-specific logic
- Operate on Tool data (knows about Tool protocol)

**Interface:**
```python
class ToolSyntax(Protocol):
    """Abstraction for tool call syntax formatting and parsing."""

    def render_documentation(self, tool: Tool) -> str:
        """
        Generate complete documentation for a tool.

        Includes:
        - Tool name and description
        - Arguments list with types/descriptions
        - Usage syntax line
        - Formatted examples

        Args:
            tool: Tool to document (pure data)

        Returns:
            Formatted documentation string
        """
        ...

    def parse(self, text: str) -> ParsedMessage:
        """
        Extract tool calls from text.

        Args:
            text: Raw text from LLM response

        Returns:
            ParsedMessage(message, tool_calls)
            - message: Text before first tool call
            - tool_calls: List of ParsedTool instances
        """
        ...
```

**Concrete Implementation:**
```python
class EmojiToolSyntax:
    """Current 🛠️-based syntax implementation."""

    def render_documentation(self, tool: Tool) -> str:
        # Formats with 🛠️ prefix and 🛠️🔚 end markers
        ...

    def parse(self, text: str) -> ParsedMessage:
        # Parses 🛠️ tool_name args\n...🛠️🔚
        ...
```

### 3. Documentation Generator

**File:** `simple_agent/application/tool_documentation.py`

**Responsibilities:**
- Generate documentation for all tools
- Use ToolSyntax to format each tool
- Apply tool-specific customizations (finalize_documentation)

**Changes:**
```python
# BEFORE (current)
def _generate_tool_documentation(tool, context: dict):
    usage_info = tool.get_usage_info()  # Tool formats itself
    usage_info = tool.finalize_documentation(usage_info, context)
    # ... format with markdown

# AFTER (new)
def _generate_tool_documentation(tool: Tool, context: dict, syntax: ToolSyntax):
    usage_info = syntax.render_documentation(tool)  # Syntax formats tool
    usage_info = tool.finalize_documentation(usage_info, context)
    # ... format with markdown
```

### 4. Message Parser

**File:** `simple_agent/application/tool_message_parser.py`

**Responsibilities:**
- Extract tool calls from LLM responses
- Use ToolSyntax to parse
- Return structured ParsedMessage

**Changes:**
```python
# BEFORE (current)
def parse_tool_calls(text: str) -> ParsedMessage:
    pattern = r'^🛠️ ([\w-]+)(?:\s+(.*))?'  # HARDCODED
    end_marker = r'^🛠️🔚'  # HARDCODED
    # ... parsing logic

# AFTER (new)
def parse_tool_calls(text: str, syntax: ToolSyntax) -> ParsedMessage:
    return syntax.parse(text)  # Syntax handles parsing
```

### 5. BaseTool Implementation

**File:** `simple_agent/tools/base_tool.py`

**Responsibilities:**
- Implement Tool protocol
- Provide default execute() behavior
- Store tool metadata (name, arguments, examples)
- **NO formatting logic** (moved to ToolSyntax)

**Changes:**
- **REMOVE** `get_usage_info()` method (no longer in protocol)
- **REMOVE** `_generate_usage_info_from_metadata()` method (moved to ToolSyntax)
- **REMOVE** `_format_example()` method (moved to ToolSyntax)
- **REMOVE** `_normalize_argument()` method (moved to ToolSyntax)
- **ADD** `@property` decorators for: `name`, `description`, `arguments`, `examples`

### 6. ParsedTool Display

**File:** `simple_agent/application/tool_library.py`

**Responsibilities:**
- Represent a parsed tool call
- Display tool calls (for logging, debugging)

**Current Issue:**
```python
def __str__(self):
    return f"🛠️ {self.name} {self.arguments}"  # HARDCODED
```

**Solution Options:**
1. Remove `__str__()` - not used for LLM output
2. Accept ToolSyntax in constructor and use it for formatting
3. Keep simple format for debugging (doesn't need to match LLM syntax)

**Recommendation:** Keep simple format - this is for human debugging, not LLM consumption.

## Related Files

### Core Files (Must Change)
- `simple_agent/application/tool_library.py` - Tool protocol
- `simple_agent/application/tool_syntax.py` - NEW - ToolSyntax abstraction
- `simple_agent/application/tool_documentation.py` - Documentation generator
- `simple_agent/application/tool_message_parser.py` - Parser
- `simple_agent/tools/base_tool.py` - BaseTool implementation

### Tool Implementation Files (No Changes Needed)
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

**Why no changes?** Tools already store examples as dicts (commit ebb268e). They're already decoupled from syntax!

## Implementation Plan: Incremental Steps

### ✅ Progress Tracking

**Current Status:** Phase 2 Complete - All Steps Finished

**Completed Steps:**
- ✅ **Phase 1, Step 1.1**: Create ToolSyntax Protocol (commit: 74e358c)
  - Created `simple_agent/application/tool_syntax.py` with ToolSyntax protocol and EmojiToolSyntax implementation
  - Created `tests/application/emoji_tool_syntax_test.py` with 12 comprehensive tests
  - All 165 tests passing
- ✅ **Phase 1, Step 1.2**: Move Formatting Logic to EmojiToolSyntax
  - Copied `_format_example()` logic from BaseTool to EmojiToolSyntax
  - Copied `_generate_usage_info_from_metadata()` logic to EmojiToolSyntax.render_documentation()
  - Copied `_normalize_argument()` helper method
  - Added 3 compatibility tests verifying EmojiToolSyntax produces identical output to BaseTool
  - All 168 tests passing
- ✅ **Phase 1, Step 1.3**: Move Parsing Logic to EmojiToolSyntax
  - Copied parsing logic from `tool_message_parser.parse_tool_calls()` to `EmojiToolSyntax.parse()`
  - Added 4 compatibility tests verifying EmojiToolSyntax.parse() produces identical results to parse_tool_calls()
  - All 172 tests passing
- ✅ **Phase 2, Step 2.1**: Add Properties to Tool Protocol
  - Added `@property` declarations for `name`, `description`, `arguments`, `examples` to Tool Protocol
  - Added TYPE_CHECKING import for ToolArgument to avoid circular dependency
  - Added method signatures for `get_usage_info()`, `execute()`, and `finalize_documentation()`
  - All 172 tests passing
- ✅ **Phase 2, Step 2.2**: Verify BaseTool Satisfies Extended Protocol
  - BaseTool class attributes (`name`, `description`, `arguments`, `examples`) satisfy Tool Protocol property requirements
  - No changes needed - Python's Protocol typing allows class attributes to satisfy property requirements
  - All 172 tests passing

**Next Step:** Phase 3, Step 3.1 - Update Documentation Generator

---

### Phase 1: Introduce ToolSyntax (No Breaking Changes)

#### ✅ Step 1.1: Create ToolSyntax Protocol [COMPLETED]
**File:** `simple_agent/application/tool_syntax.py` (NEW)
- Define `ToolSyntax` protocol with `render_documentation()` and `parse()` methods
- Create `EmojiToolSyntax` implementation with current 🛠️ logic
- **No existing code changes yet**
- **Tests:** Unit tests for EmojiToolSyntax formatting and parsing

**Safety:** New file, no risk to existing code.
**Status:** ✅ COMPLETED - commit 74e358c

#### ✅ Step 1.2: Move Formatting Logic to EmojiToolSyntax [COMPLETED]
- Copy `_format_example()` logic from BaseTool → `EmojiToolSyntax`
- Copy `_generate_usage_info_from_metadata()` logic → `EmojiToolSyntax.render_documentation()`
- **Don't remove from BaseTool yet** - duplicate for now
- **Tests:** Verify EmojiToolSyntax produces identical output to BaseTool

**Safety:** Duplication ensures existing code still works.
**Status:** ✅ COMPLETED - All 168 tests passing

#### ✅ Step 1.3: Move Parsing Logic to EmojiToolSyntax [COMPLETED]
- Copy parsing logic from `tool_message_parser.py` → `EmojiToolSyntax.parse()`
- **Don't remove from parser yet** - duplicate for now
- **Tests:** Verify EmojiToolSyntax.parse() produces identical results

**Safety:** Duplication ensures existing parser still works.
**Status:** ✅ COMPLETED - All 172 tests passing

### Phase 2: Extend Tool Protocol (Backward Compatible)

#### ✅ Step 2.1: Add Properties to Tool Protocol [COMPLETED]
**File:** `simple_agent/application/tool_library.py`
- **ADD** properties: `description`, `arguments`, `examples`
- **KEEP** `get_usage_info()` method (for backward compatibility)
- **Tests:** Verify BaseTool satisfies extended protocol

**Safety:** Additive change, no breaking changes.
**Status:** ✅ COMPLETED - All 172 tests passing

#### ✅ Step 2.2: Verify BaseTool Satisfies Extended Protocol [COMPLETED]
**File:** `simple_agent/tools/base_tool.py`
- Verify existing class attributes satisfy Tool Protocol property requirements
- No changes needed - Python's Protocol typing accepts class attributes for properties
- **Tests:** Verify all tools still work

**Safety:** No code changes, fully backward compatible.
**Status:** ✅ COMPLETED - All 172 tests passing

### Phase 3: Switch to ToolSyntax (Breaking Change, Careful!)

#### Step 3.1: Update Documentation Generator
**File:** `simple_agent/application/tool_documentation.py`
- Create global `CURRENT_SYNTAX = EmojiToolSyntax()`
- Update `_generate_tool_documentation()` to accept `syntax` parameter
- **Fallback:** Try `syntax.render_documentation(tool)`, fall back to `tool.get_usage_info()` if not available
- **Tests:** Verify generated documentation unchanged

**Safety:** Fallback ensures backward compatibility.

#### Step 3.2: Update Message Parser
**File:** `simple_agent/application/tool_message_parser.py`
- Create global `CURRENT_SYNTAX = EmojiToolSyntax()`
- Update `parse_tool_calls()` to accept `syntax` parameter with default
- Use `syntax.parse(text)` instead of hardcoded parsing
- Keep old parsing logic temporarily for comparison
- **Tests:** Verify parsing results unchanged

**Safety:** Default parameter and comparison ensure safety.

#### Step 3.3: Update BaseTool to Delegate
**File:** `simple_agent/tools/base_tool.py`
- Import `CURRENT_SYNTAX`
- Change `get_usage_info()` to call `CURRENT_SYNTAX.render_documentation(self)`
- **Keep** old methods as fallback for custom tools
- **Tests:** Verify all tool documentation unchanged

**Safety:** Delegation with fallback ensures compatibility.

### Phase 4: Remove Old Code (Cleanup)

#### Step 4.1: Remove get_usage_info() from Tool Protocol
**File:** `simple_agent/application/tool_library.py`
- Remove `get_usage_info()` from Tool protocol
- **Tests:** Verify all code uses ToolSyntax, not tool.get_usage_info()

**Safety:** This is the breaking change - only do after Step 3 complete.

#### Step 4.2: Remove Formatting Methods from BaseTool
**File:** `simple_agent/tools/base_tool.py`
- Remove `get_usage_info()` method
- Remove `_generate_usage_info_from_metadata()` method
- Remove `_format_example()` method
- Remove `_normalize_argument()` method
- **Tests:** Full test suite

**Safety:** All formatting now handled by ToolSyntax.

#### Step 4.3: Remove Hardcoded Parsing from Parser
**File:** `simple_agent/application/tool_message_parser.py`
- Remove old regex patterns
- Remove fallback/comparison code
- **Tests:** Full test suite

**Safety:** Parser fully uses ToolSyntax.

## Success Criteria

After implementation:

1. ✅ Tool protocol is pure data (no formatting methods)
2. ✅ All syntax logic centralized in ToolSyntax implementations
3. ✅ Zero changes needed in tool implementation files
4. ✅ All tests pass
5. ✅ Changing syntax would require changing only 1 location: `CURRENT_SYNTAX = NewSyntax()`
