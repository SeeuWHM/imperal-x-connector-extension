"""HTTP client — calls the shared x-connector-api backend microservice.

Same contract as meta-social-extension/api_client.py — every call carries
`backend_jwt` (extension identity) and `X-Imperal-Id` (caller's tenant).
This extension never sees a raw X access token — the backend owns that
entirely.
"""
from __future__ import annotations

import httpx

from imperal_sdk.types import ActionResult

from app import SERVER_URL

TIMEOUT = 30


def _normalize_backend_url(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    return value.rstrip("/")


def _err(data: dict) -> ActionResult:
    """The one place every handler builds an error ActionResult from a
    call_backend() result — always carries a structured code + retryable."""
    return ActionResult.error(
        error=data.get("error", "unknown error"),
        retryable=bool(data.get("_retryable", False)),
        code=data.get("error_code", "") or "INTERNAL",
    )


async def call_backend(ctx, method: str, path: str, params: dict | None = None,
                        json: dict | None = None, timeout: int = TIMEOUT) -> dict:
    """Call x-connector-api. Returns the parsed JSON body, or
    {"error": ..., "error_code": ..., "_retryable": bool}."""
    base_url = _normalize_backend_url(SERVER_URL)
    if not base_url:
        return {
            "error": "X Connector backend URL is not configured.",
            "error_code": "BACKEND_NOT_CONFIGURED", "_config": True,
        }

    backend_jwt = await ctx.secrets.get("backend_jwt")
    if not backend_jwt:
        return {
            "error": "X Connector backend is not configured on our side yet — this has been logged.",
            "error_code": "BACKEND_NOT_CONFIGURED", "_config": True,
        }

    headers = {
        "Authorization": f"Bearer {backend_jwt}",
        "X-Imperal-Id": ctx.user.imperal_id,
    }

    url = f"{base_url}{path}"
    try:
        if method.upper() == "GET":
            resp = await ctx.http.get(url, params=params or {}, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            resp = await ctx.http.post(url, params=params or {}, json=json or {}, headers=headers, timeout=timeout)
        elif method.upper() == "DELETE":
            resp = await ctx.http.delete(url, params=params or {}, headers=headers, timeout=timeout)
        else:
            return {"error": f"Unsupported method {method}", "error_code": "INTERNAL", "_config": True}
    except httpx.TimeoutException:
        return {
            "error": "X Connector backend timed out — please retry.",
            "error_code": "BACKEND_TIMEOUT", "_retryable": True,
        }
    except httpx.HTTPError as exc:
        return {
            "error": f"X Connector backend is unreachable — this has been logged ({exc.__class__.__name__}).",
            "error_code": "BACKEND_5XX", "_retryable": True,
        }

    if resp.status_code == 401:
        return {
            "error": "X Connector backend rejected our credentials — this has been logged.",
            "error_code": "PERMISSION_DENIED", "_config": True,
        }
    if resp.status_code == 404:
        return {"error": "Not found.", "error_code": "NOT_FOUND", "_config": True}
    if resp.status_code >= 500:
        detail = resp.body if isinstance(resp.body, dict) else {"detail": resp.body}
        msg = detail.get("detail", detail) if isinstance(detail, dict) else detail
        return {
            "error": f"X Connector backend error: {msg}",
            "error_code": "BACKEND_5XX", "_retryable": True,
        }
    if resp.status_code >= 400:
        detail = resp.body if isinstance(resp.body, dict) else {"detail": resp.body}
        msg = detail.get("detail", detail) if isinstance(detail, dict) else detail
        return {"error": f"X Connector error: {msg}", "error_code": "BACKEND_REJECTED"}

    return resp.body if isinstance(resp.body, dict) else {"data": resp.body}
