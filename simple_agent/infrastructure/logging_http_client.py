import json
import logging
from typing import Any, Iterable

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


def _format_request(request: httpx.Request) -> str:
    http_version = request.extensions.get("http_version", "HTTP/1.1")
    if isinstance(http_version, bytes):
        http_version = http_version.decode("ascii", errors="replace")

    target = request.url.raw_path.decode("ascii", errors="replace")
    if not target:
        target = "/"

    lines = [f"{request.method} {target} {http_version}"]
    lines.extend(_format_headers(request.headers))

    body = _format_body(request.headers.get("content-type"), request.content, None)
    if body:
        lines.append("")
        lines.append(body)

    return "\n" + "\n".join(lines)


def _format_response(response: httpx.Response) -> str:
    http_version = response.http_version or "HTTP/1.1"
    reason = response.reason_phrase or ""
    status_line = f"{http_version} {response.status_code} {reason}".strip()

    lines = [status_line]
    lines.extend(_format_headers(response.headers))

    body = _format_body(response.headers.get("content-type"), response.content, getattr(response, "encoding", None))
    if body:
        lines.append("")
        lines.append(body)

    return "\n" + "\n".join(lines)


def _format_headers(headers: httpx.Headers) -> Iterable[str]:
    return [
        f"{_format_header_name(name)}: {_mask_header_value(name, value)}"
        for name, value in headers.items()
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
