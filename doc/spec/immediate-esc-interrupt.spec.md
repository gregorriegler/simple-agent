# Immediate ESC Interrupt

## Problem

When pressing ESC during an agent session, the interruption is not immediate. Currently:
- ESC waits for the running tool to finish
- ESC waits for the LLM response to complete
- Only then does the "Session interrupted" message appear

**Root cause**: The agent loop in `agent.py:69-106` uses synchronous blocking calls:
- `llm_responds()` blocks on `requests.post()` until the LLM finishes
- `execute_tool()` blocks until tool completion
- The escape flag is only checked after these calls return

**Expected behavior**: ESC immediately aborts both the running tool and pending LLM request.

## Solution

Convert blocking operations to async with cancellation support. Propagate async bottom-up, with each caller wrapping in `asyncio.run()` until we reach the UI layer.

### Implementation Steps

Each step keeps all existing tests passing. Async "bubbles up" naturally.

#### DONE - Async LLM protocol and llm_responds

7. ✅ **Fix async method naming in LLM clients**
   - Rename `__call___async` → `call_async` (fix typo, make public)
   - All 4 clients: Claude, OpenAI, Gemini, Gemini v1
   - Tests pass (no behavior change)

8. ✅ **Add `call_async` to LLM Protocol**
   - Add `async def call_async(...)` to `LLM` Protocol in `llm.py`
   - Tests pass (protocol just gains a method)

9. ✅ **Add `call_async` to LLM stubs used in tests**
   - Update `StubLLM` / `create_llm_stub` to have `call_async`
   - Tests pass

10. ✅ **Make `agent.llm_responds` async**
    - Change `def llm_responds` → `async def llm_responds`
    - Call `await self.llm.call_async(...)` instead of `self.llm(...)`
    - Caller (`run_tool_loop`) wraps with `asyncio.run()`
    - Tests pass

#### NOW - Async tool execution and run_tool_loop

10a. **Cleanup: Remove dead sync `__call__` methods in test stubs**
    - `tests/session_test_bed.py`: `DefaultLLM.__call__` (line 50) - unused, needs `call_async`
    - `tests/session_test_bed.py`: `FailingLLM.__call__` (line 72) - redundant, `call_async` exists
    - Tests pass

11. **Make `agent.execute_tool` async**
    - Change `def execute_tool` → `async def execute_tool`
    - No internal async calls yet (just preparation for cancellation)
    - Caller (`run_tool_loop`) wraps with `asyncio.run()` 
    - Tests pass

12. **Make `agent.run_tool_loop` async**
    - Change `def run_tool_loop` → `async def run_tool_loop`
    - Use `await llm_responds()` and `await execute_tool()` directly
    - Remove internal `asyncio.run()` calls
    - Caller (`start`) wraps with `asyncio.run()`
    - Tests pass

#### LATER - Feature completion

13. Write failing test for immediate interrupt (TDD)
14. Wire up cancellation in `textual_app`
15. Remove sync wrappers

### Components changed (NOW phase)

- `tests/session_test_bed.py` - cleanup dead `__call__` methods, add `call_async` to `DefaultLLM`
- `simple_agent/application/agent.py` - make `execute_tool` async, then `run_tool_loop` async

