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

#### NOW - Async LLM protocol and llm_responds

7. **Fix async method naming in LLM clients**
   - Rename `__call___async` → `call_async` (fix typo, make public)
   - All 4 clients: Claude, OpenAI, Gemini, Gemini v1
   - Tests pass (no behavior change)

8. **Add `call_async` to LLM Protocol**
   - Add `async def call_async(...)` to `LLM` Protocol in `llm.py`
   - Tests pass (protocol just gains a method)

9. **Add `call_async` to LLM stubs used in tests**
   - Update `StubLLM` / `create_llm_stub` to have `call_async`
   - Tests pass

#### NEXT - Async tool execution and run_tool_loop

10. **Make `agent.llm_responds` async**
  - Change `def llm_responds` → `async def llm_responds`
  - Call `await self.llm.call_async(...)` instead of `self.llm(...)`
  - Caller (`run_tool_loop`) wraps with `asyncio.run()`
  - Tests pass

11. Tool execution → async
12. `agent.run_tool_loop` → async

Details to be specified when we get here.

#### LATER - Feature completion

13. Write failing test for immediate interrupt (TDD)
14. Wire up cancellation in `textual_app`
15. Remove sync wrappers

### Components changed (NOW phase)

- `simple_agent/infrastructure/claude/claude_client.py` - rename `__call___async` → `call_async`
- `simple_agent/infrastructure/openai/openai_client.py` - rename `__call___async` → `call_async`
- `simple_agent/infrastructure/gemini/gemini_client.py` - rename `__call___async` → `call_async`
- `simple_agent/infrastructure/gemini/gemini_v1_client.py` - rename `__call___async` → `call_async`
- `simple_agent/application/llm.py` - add `call_async` to Protocol
- `simple_agent/application/llm_stub.py` - add `call_async` to stub
- `simple_agent/application/agent.py` - make `llm_responds` async

