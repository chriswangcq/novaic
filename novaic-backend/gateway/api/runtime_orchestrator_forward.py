"""Helpers for forwarding Gateway public APIs to Runtime Orchestrator."""

from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from common.config import ServiceConfig
from common.http.clients import internal_client


def forward_to_runtime_orchestrator(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Forward one public API call to Runtime Orchestrator."""
    base_url = ServiceConfig.RUNTIME_ORCHESTRATOR_URL.rstrip("/")
    if not base_url:
        raise HTTPException(
            status_code=500,
            detail="Runtime Orchestrator URL is not configured",
        )

    url = f"{base_url}{path}"
    try:
        with internal_client(timeout=ServiceConfig.HTTP_TIMEOUT) as client:
            response = client.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_body,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail: Any = e.response.text
        try:
            payload = e.response.json()
            detail = payload.get("detail", payload)
        except Exception:
            pass
        raise HTTPException(status_code=e.response.status_code, detail=detail) from e
    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Runtime Orchestrator timeout: {url}",
        ) from e
    except httpx.ConnectError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Runtime Orchestrator unavailable: {base_url}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Runtime Orchestrator request failed: {e}",
        ) from e

    if not response.text:
        return {"success": True}

    try:
        return response.json()
    except Exception:
        return {"success": True, "raw": response.text}
