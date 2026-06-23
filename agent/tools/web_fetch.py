"""Web fetch tool — retrieve content from a URL."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HTTPX_AVAILABLE = False

DEFAULT_TIMEOUT = 30
MAX_RESPONSE_BYTES = 100_000


async def web_fetch_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch a URL and return its response body.

    Step params:
        url (str): The URL to fetch.
        method (str): HTTP method (default GET).
        timeout (int): Request timeout in seconds (default 30).
    """
    if not _HTTPX_AVAILABLE:
        return {"status": "error", "error": "httpx is not installed"}

    params = step.get("params", {})
    url = params.get("url", "")
    method = params.get("method", "GET").upper()
    timeout = params.get("timeout", DEFAULT_TIMEOUT)

    if not url:
        return {"status": "error", "error": "No URL provided"}

    logger.info("Fetching %s %s", method, url)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, url)

        body = response.text[:MAX_RESPONSE_BYTES]

        return {
            "status": "ok",
            "url": url,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "body": body,
            "size": len(response.text),
        }

    except httpx.TimeoutException:
        return {"status": "error", "error": f"Request to {url} timed out"}
    except httpx.RequestError as exc:
        return {"status": "error", "error": f"Request failed: {exc}"}
