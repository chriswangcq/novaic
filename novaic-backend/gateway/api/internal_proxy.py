"""
Gateway /internal proxy router.

Gateway acts as an API aggregator and forwards internal orchestration APIs to
Runtime Orchestrator. It does not execute internal runtime/subagent/message
logic locally.
"""

from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse, Response

from common.config import ServiceConfig
from common.http.clients import internal_async_client

router = APIRouter(prefix="/internal", tags=["internal-proxy"])


def _build_target_url(path: str) -> str:
    base = (ServiceConfig.RUNTIME_ORCHESTRATOR_URL or "").rstrip("/")
    if not base:
        raise RuntimeError("Runtime Orchestrator URL is not configured")
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{base}/internal{normalized}"


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_internal(path: str, request: Request):
    """Forward /internal/* requests to Runtime Orchestrator."""
    try:
        target = _build_target_url(path)
    except RuntimeError as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

    body = await request.body()
    content_type: Optional[str] = request.headers.get("content-type")
    headers = {"content-type": content_type} if content_type else None

    try:
        async with internal_async_client(timeout=30.0) as client:
            upstream = await client.request(
                method=request.method,
                url=target,
                params=dict(request.query_params),
                content=body if body else None,
                headers=headers,
            )
        media_type = upstream.headers.get("content-type") or "application/json"
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            media_type=media_type,
        )
    except httpx.ConnectError as e:
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Runtime Orchestrator unavailable: {e}",
            },
        )
    except httpx.TimeoutException as e:
        return JSONResponse(
            status_code=504,
            content={
                "detail": f"Runtime Orchestrator timeout: {e}",
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={
                "detail": f"Runtime Orchestrator proxy error: {e}",
            },
        )
