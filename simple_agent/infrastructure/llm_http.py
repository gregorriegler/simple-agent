import asyncio

import httpx

from simple_agent.infrastructure.logging_http_client import LoggingAsyncClient

MAX_RETRY_AFTER = 60


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
            if attempt < max_retries and _is_transient(error):
                await asyncio.sleep(_retry_after(error) or retry_delay)
                continue

            raise error_class(
                f"API request failed: {error}{_response_details(error)}"
            ) from error

    raise error_class("API request failed: no response")


def _is_transient(error: Exception) -> bool:
    if isinstance(error, httpx.TimeoutException):
        return True
    if not isinstance(error, httpx.HTTPStatusError):
        return False
    if error.response.status_code == 500:
        return True
    return _api_error_code(error.response) == "malformed_tool_call"


def _retry_after(error: Exception) -> float | None:
    if not isinstance(error, httpx.HTTPStatusError):
        return None
    try:
        seconds = float(error.response.headers.get("Retry-After", ""))
    except ValueError:
        return None
    return min(seconds, MAX_RETRY_AFTER)


def _api_error_code(response: httpx.Response) -> str | None:
    try:
        body = response.json()
    except ValueError:
        return None
    api_error = body.get("error") if isinstance(body, dict) else None
    return api_error.get("code") if isinstance(api_error, dict) else None


def _response_details(error: Exception) -> str:
    """
    Quote the API error envelope of a failed response.

    Only the recognized envelope is quoted: an error body from a proxy or
    gateway can echo the request, credentials included, and this ends up in
    the session log.
    """
    if not isinstance(error, httpx.HTTPStatusError):
        return ""

    try:
        body = error.response.json()
    except ValueError:
        return ""

    api_error = body.get("error") if isinstance(body, dict) else None
    if not isinstance(api_error, dict):
        return ""

    label = api_error.get("status") or api_error.get("type") or api_error.get("code")
    message = api_error.get("message")
    details = ": ".join(str(part) for part in (label, message) if part)
    return f" - {details[:500]}" if details else ""
