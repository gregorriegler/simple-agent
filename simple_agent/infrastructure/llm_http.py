import asyncio

import httpx

from simple_agent.infrastructure.logging_http_client import LoggingAsyncClient


async def post_with_retry(
    url: str,
    *,
    headers: dict[str, str],
    json: dict,
    timeout: float,
    error_class: type[Exception],
    transport: httpx.AsyncBaseTransport | None = None,
    max_retries: int = 5,
    retry_delay: float = 2,
) -> httpx.Response:
    for attempt in range(max_retries + 1):
        try:
            async with LoggingAsyncClient(
                timeout=timeout, transport=transport
            ) as client:
                response = await client.post(url, headers=headers, json=json)
            response.raise_for_status()
            return response
        except (httpx.RequestError, httpx.HTTPStatusError) as error:
            should_retry = attempt < max_retries and (
                isinstance(error, httpx.TimeoutException)
                or (
                    isinstance(error, httpx.HTTPStatusError)
                    and error.response.status_code == 500
                )
            )

            if should_retry:
                await asyncio.sleep(retry_delay)
                continue

            raise error_class(f"API request failed: {error}") from error

    raise error_class("API request failed: no response")
