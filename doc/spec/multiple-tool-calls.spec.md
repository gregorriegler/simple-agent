# Multiple Tool Calls Per Response

## Problem

Currently, when the LLM responds with multiple tool calls in a single answer, only the first tool is executed (line 84 in `agent.py`: `self.execute_tool(tools[0])`). The parser already supports extracting multiple tool calls, but the execution logic ignores all but the first.

This limits agent efficiency—requiring multiple LLM round-trips for tasks that could be done in one response.

## Solution

Execute all parsed tool calls sequentially within `agent.py`:

1. **Sequential execution**: Iterate over all tools in `tools` list, executing each in order
2. **Stop on failure**: If any tool returns `success=False`, stop executing remaining tools
3. **Combined result message**: Aggregate all tool results into a single user message for context
4. **Ignore CompleteResult for continuation**: Only check the final tool's result to determine if the loop should continue

### Code Changes

**In `run_tool_loop`**: Replace single tool execution with a loop over all tools.

**In `execute_tool`**: Remove the line that adds to context (`self.context.user_says(...)`). Instead, the caller (`run_tool_loop`) will aggregate results and add one combined message.

**Combined message format**:
```
Result of 🛠️ tool1 args
<result1>

Result of 🛠️ tool2 args
<result2>
```

### Relevant Files
- [simple_agent/application/agent.py](../../simple_agent/application/agent.py) - execution loop
- [simple_agent/application/tool_library.py](../../simple_agent/application/tool_library.py) - ToolResult, ContinueResult