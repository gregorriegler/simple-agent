import pytest
import logging
import httpx
from approvaltests import verify

from simple_agent.infrastructure.logging_http_client import LoggingAsyncClient

class LogContent:
    def __init__(self, caplog):
        self.caplog = caplog
        
    def __str__(self):
        # Extract only the message part from the log records to ensure stable approval tests
        # that don't depend on log levels, line numbers or timestamps.
        return "\n".join(
            record.message 
            for record in self.caplog.records 
            if "simple_agent.infrastructure.logging_http_client" in record.name
        )

@pytest.mark.asyncio
async def test_logging_async_client_json_interaction(caplog):
    response_data = {"result": "success"}
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data, headers={"Content-Type": "application/json"})
    )

    with caplog.at_level(logging.DEBUG, logger="simple_agent.infrastructure.logging_http_client"):
        async with LoggingAsyncClient(transport=transport) as client:
            await client.post(
                "https://api.example.com/test",
                json={"key": "value"},
                headers={"X-Test-Header": "test-value"}
            )

    verify(LogContent(caplog))

@pytest.mark.asyncio
async def test_logging_async_client_data_interaction(caplog):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content="plain text response", headers={"Content-Type": "text/plain"})
    )

    with caplog.at_level(logging.DEBUG, logger="simple_agent.infrastructure.logging_http_client"):
        async with LoggingAsyncClient(transport=transport) as client:
            await client.post(
                "https://api.example.com/test",
                content="plain text body"
            )

    verify(LogContent(caplog))


@pytest.mark.asyncio
async def test_logging_async_client_masks_sensitive_headers(caplog):
    response_data = {"result": "success"}
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data, headers={"Content-Type": "application/json"})
    )

    with caplog.at_level(logging.DEBUG, logger="simple_agent.infrastructure.logging_http_client"):
        async with LoggingAsyncClient(transport=transport) as client:
            await client.post(
                "https://api.example.com/test",
                json={"key": "value"},
                headers={
                    "Authorization": "Bearer secret-token",
                    "X-Api-Key": "secret-key",
                    "X-Test-Header": "test-value"
                }
            )

    verify(LogContent(caplog))
