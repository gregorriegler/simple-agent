import json
import logging
from collections.abc import Iterable
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SENSITIVE_HEADERS = {"authorization", "x-api-key"}


class LoggingAsyncClient(httpx.AsyncClient):
    async def request(
        self,
        method: str,
        url: httpx.URL | str,
        *,
        content: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
        json: Any | None = None,
        params: Any | None = None,
        headers: Any | None = None,
        cookies: Any | None = None,
        auth: Any | None = httpx.USE_CLIENT_DEFAULT,
        follow_redirects: bool | Any = httpx.USE_CLIENT_DEFAULT,
        timeout: Any = httpx.USE_CLIENT_DEFAULT,
        extensions: Any | None = None,
    ) -> httpx.Response:
        request = self.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )

        logger.debug(_format_request(request))

        response = await self.send(
            request,
            auth=auth,
            follow_redirects=follow_redirects,
        )

        logger.debug(_format_response(response))

        return response


def format_request_args(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | str | None,
    http_version: str = "HTTP/1.1",
) -> str:
    lines = [f"{method} {url} {http_version}"]
    lines.extend(_format_headers(headers))

    content_type = None
    for k, v in headers.items():
        if k.lower() == "content-type":
            content_type = v
            break

    body_str = _format_body(content_type, body, None)
    if body_str:
        lines.append("")
        lines.append(body_str)

    return "\n" + "\n".join(lines)


def format_response_args(
    status_code: int,
    headers: dict[str, str],
    body: bytes | str | None,
    reason_phrase: str = "",
    http_version: str = "HTTP/1.1",
    encoding: str | None = None,
) -> str:
    status_line = f"{http_version} {status_code} {reason_phrase}".strip()

    lines = [status_line]
    lines.extend(_format_headers(headers))

    content_type = None
    for k, v in headers.items():
        if k.lower() == "content-type":
            content_type = v
            break

    body_str = _format_body(content_type, body, encoding)
    if body_str:
        lines.append("")
        lines.append(body_str)

    return "\n" + "\n".join(lines)


def _format_request(request: httpx.Request) -> str:
    http_version = request.extensions.get("http_version", "HTTP/1.1")
    if isinstance(http_version, bytes):
        http_version = http_version.decode("ascii", errors="replace")

    target = request.url.raw_path.decode("ascii", errors="replace")
    if not target:
        target = "/"

    return format_request_args(
        method=request.method,
        url=target,
        headers=dict(request.headers),
        body=request.content,
        http_version=http_version,
    )


def _format_response(response: httpx.Response) -> str:
    http_version = response.http_version or "HTTP/1.1"
    reason = response.reason_phrase or ""

    return format_response_args(
        status_code=response.status_code,
        headers=dict(response.headers),
        body=response.content,
        reason_phrase=reason,
        http_version=http_version,
        encoding=getattr(response, "encoding", None),
    )


def _format_headers(
    headers: Iterable[tuple[str, str]] | dict[str, str],
) -> Iterable[str]:
    header_items = headers.items() if isinstance(headers, dict) else headers
    return [
        f"{_format_header_name(name)}: {_mask_header_value(name, value)}"
        for name, value in header_items
    ]


def _format_header_name(name: str) -> str:
    return "-".join(part[:1].upper() + part[1:].lower() for part in name.split("-"))


def _mask_header_value(name: str, value: str) -> str:
    if name.lower() in SENSITIVE_HEADERS:
        return "****"
    return value


def _format_body(
    content_type: str | None,
    body: bytes | str | None,
    encoding: str | None,
) -> str:
    if body is None or body == b"" or body == "":
        return ""

    if isinstance(body, str):
        body_text = body
    else:
        decode_with = encoding or "utf-8"
        body_text = body.decode(decode_with, errors="replace")

    if content_type and "application/json" in content_type:
        try:
            parsed = json.loads(body_text)
        except json.JSONDecodeError:
            return body_text
        return json.dumps(parsed, indent=2, ensure_ascii=False)

    return body_text
