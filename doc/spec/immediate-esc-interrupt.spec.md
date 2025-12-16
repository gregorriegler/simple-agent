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

#### NOW - Async LLM adapters

1. ~~**Refactor LLM adapter tests to use `pytest-httpserver`**~~
   - ~~Decouple tests from HTTP implementation (`requests` vs `httpx`)~~
   - ~~Tests verify correct HTTP calls and response handling~~
   - ~~After this, tests are implementation-agnostic~~

2. ~~**Add `httpx` dependency**~~

3. ~~**Claude adapter → async with httpx**~~
   - ~~Replace `requests.post` with `await httpx.AsyncClient.post()`~~
   - ~~Caller (`agent.llm_responds`) wraps with `asyncio.run()`~~
   - ~~Existing tests pass unchanged (thanks to step 1)~~

4. **Other LLM adapters → async**
   - OpenAI, Gemini, Gemini v1
   - Same pattern: async internally, caller wraps

#### NEXT - Async agent internals

5. `agent.llm_responds` → async
6. Tool execution → async
7. `agent.run_tool_loop` → async

Details to be specified when we get here (test strategy for agent tests TBD).

#### LATER - Feature completion

8. Write failing test for immediate interrupt (TDD)
9. Wire up cancellation in `textual_app`
10. Remove sync wrappers

### Components changed

- `tests/infrastructure/*_client_test.py` - use pytest-httpserver
- `simple_agent/infrastructure/claude/claude_client.py`
- `simple_agent/infrastructure/openai/openai_client.py`
- `simple_agent/infrastructure/gemini/gemini_client.py`
- `simple_agent/infrastructure/gemini/gemini_v1_client.py`
- `simple_agent/application/agent.py`
- `simple_agent/application/tool_library.py`
- `simple_agent/infrastructure/textual/textual_app.py`

