import asyncio
import concurrent.futures


def run_async_safely(coro):
    """
    Run an async coroutine, handling both top-level and nested event loop contexts.
    
    - If no event loop is running: creates one with asyncio.run()
    - If event loop is already running: runs in a thread to avoid nesting
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        loop = asyncio.get_running_loop()
        # Event loop is already running (nested context, e.g., subagent)
        # Run in a thread to avoid nested event loop error
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(lambda: asyncio.run(coro))
        result = future.result()
        executor.shutdown(wait=True)
        return result
    except RuntimeError:
        # No event loop running, create one
        return asyncio.run(coro)