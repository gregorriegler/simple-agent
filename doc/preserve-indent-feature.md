# Preserve-Indent Feature Specification

## Overview
Auto-preserve indentation when editing files. Enabled by default, can be disabled with `--raw` flag.

## Behavior

### Replace Mode
- Detect leading whitespace from the **first line being replaced**
- Apply that indentation to new content (if new content doesn't already start with whitespace)

### Insert Mode
- Detect leading whitespace from the **line at the insertion point**
- Apply that indentation to new content (if new content doesn't already start with whitespace)
- If inserting beyond file end, no indentation added

### Delete Mode
- No indentation processing (N/A)

### Multi-line Content
- Only process the first line of new content
- Subsequent lines use whatever indentation they have

## Files to Change

### 1. `simple_agent/tools/edit_file_tool.py`
- Add `raw` field to `EditFileArgs` dataclass
- Update `_parse_arguments` to detect `--raw` flag
- Add method: `_detect_indentation(lines, line_number) -> str`
- Add method: `_apply_indentation(content, indent, raw_mode) -> str`
- Modify `_perform_file_edit` to apply indentation in replace/insert operations
- Update tool description and examples

### 2. `tests/edit_file_tool_test.py`
- Add new test cases (see below)

## Test Cases

Adapt existing tests and make sure redundant ones are removed.

```python
def test_edit_file_replace_with_auto_indent_python(tmp_path):
    initial_content = "line1\n    existing = 1\nline3"
    command = "🛠️ edit-file test.py replace 2 new = 2"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
    # Expected: "line1\n    new = 2\nline3"

def test_edit_file_replace_with_raw_flag(tmp_path):
    initial_content = "line1\n    existing = 1\nline3"
    command = "🛠️ edit-file test.py replace 2 --raw new = 2"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
    # Expected: "line1\nnew = 2\nline3"

def test_edit_file_insert_with_auto_indent(tmp_path):
    initial_content = "line1\n    line2\nline3"
    command = "🛠️ edit-file test.py insert 2 new_line"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
    # Expected: "line1\n    new_line\n    line2\nline3"

def test_edit_file_insert_with_raw_flag(tmp_path):
    initial_content = "line1\n    line2\nline3"
    command = "🛠️ edit-file test.py insert 2 --raw new_line"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
    # Expected: "line1\nnew_line\n    line2\nline3"

def test_edit_file_replace_preserves_manual_indentation(tmp_path):
    initial_content = "line1\n    existing\nline3"
    command = "🛠️ edit-file test.py replace 2         manually_indented"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
    # Expected: "line1\n        manually_indented\nline3" (keeps 8 spaces)

def test_edit_file_replace_multiline_only_indents_first_line(tmp_path):
    initial_content = "line1\n    existing\nline3"
    command = "🛠️ edit-file test.py replace 2 line1\nline2\n    line3"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
    # Expected: "line1\n    line1\nline2\n    line3\nline3"

def test_edit_file_insert_beyond_file_end_no_indentation(tmp_path):
    initial_content = "line1\nline2"
    command = "🛠️ edit-file test.py insert 10 new_content"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
    # Expected: no indentation added to new_content

def test_edit_file_replace_with_tabs(tmp_path):
    initial_content = "line1\n\texisting\nline3"
    command = "🛠️ edit-file test.py replace 2 new_line"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
    # Expected: "line1\n\tnew_line\nline3" (preserves tab)

def test_edit_file_insert_at_unindented_line(tmp_path):
    initial_content = "line1\nline2\n    line3"
    command = "🛠️ edit-file test.py insert 2 new_line"
    verify_edit_tool(library, "test.py", initial_content, command, tmp_path=tmp_path)
```
