# Bubble-up async refactor

In this refactoring synchronous API boundary is preserved by moving `asyncio.run(...)` upward from callee to caller.

Goal: show how **A stays a blocking API** while **B becomes an async API**, keeping existing sync tests passing as long as they call `A()`.

## Before

A (blocking API) → B (blocking API).  
B does async work internally but hides it behind a sync wrapper.

```python
import asyncio

async def _B_async():
    return 123

def B():          # blocking API
    return asyncio.run(_B_async())

def A():          # blocking API
    return B() + 1

# ✅ Tests pass here as long as tests call A() (sync)
```

## After

A remains a blocking API and now does the wrapping.
B becomes an async API wrapper around the existing internal async implementation (_B_async).

```python
import asyncio

async def _B_async():
  return 123

async def B():    # async API
  return await _B_async()

def A():          # blocking API
  return asyncio.run(B()) + 1

# ✅ Tests pass here as long as tests call A() (sync)
```
