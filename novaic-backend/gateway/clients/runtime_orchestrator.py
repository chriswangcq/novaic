"""
Runtime Orchestrator client.

This client is introduced for Phase 4 split. RUNTIME_ORCHESTRATOR_URL is now
default-on; Gateway depends strictly on Runtime Orchestrator at startup.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from common.config import ServiceConfig
from common.http.clients import internal_async_client

logger = logging.getLogger(__name__)

# Timeout for startup health check (shorter than normal requests)
_HEALTH_CHECK_TIMEOUT = 5.0


async def check_runtime_orchestrator_health() -> None:
    """
    Strict health check for Runtime Orchestrator at Gateway startup.

    Uses ServiceConfig.RUNTIME_ORCHESTRATOR_URL and calls GET /api/health.
    Raises RuntimeError on non-200, timeout, or any exception.
    No fallback; Gateway must not start without a healthy orchestrator.
    """
    base_url = ServiceConfig.RUNTIME_ORCHESTRATOR_URL.rstrip("/")
    if not base_url:
        raise RuntimeError(
            "Runtime Orchestrator URL is not configured; Gateway cannot start"
        )
    url = f"{base_url}/api/health"
    try:
        async with internal_async_client(timeout=_HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Runtime Orchestrator health check failed: "
                    f"GET {url} returned {response.status_code}"
                )
    except httpx.TimeoutException as e:
        raise RuntimeError(
            f"Runtime Orchestrator health check timed out: GET {url}",
        ) from e
    except httpx.ConnectError as e:
        raise RuntimeError(
            f"Runtime Orchestrator unreachable: {base_url}",
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Runtime Orchestrator health check failed: {e}",
        ) from e


class RuntimeOrchestratorClient:
    """HTTP client for external Runtime Orchestrator service."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or ServiceConfig.RUNTIME_ORCHESTRATOR_URL
        if not self.base_url:
            raise ValueError("Runtime Orchestrator URL is not configured")
        self.client = internal_async_client(
            base_url=self.base_url,
            timeout=ServiceConfig.HTTP_TIMEOUT,
        )
        logger.info(
            "[RuntimeOrchestratorClient] Initialized with base_url=%s", self.base_url
        )

    @classmethod
    def is_enabled(cls) -> bool:
        """Whether Runtime Orchestrator proxy mode is configured."""
        return bool(ServiceConfig.RUNTIME_ORCHESTRATOR_URL)

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self.client.aclose()

    async def forward(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Forward one internal request to Runtime Orchestrator.

        Args:
            method: HTTP method, such as GET/POST/PATCH/DELETE.
            path: Absolute path expected by orchestrator, e.g.
                "/internal/runtimes/list".
            params: Optional query parameters.
            json: Optional json body.
        """
        response = await self.client.request(
            method=method.upper(),
            url=path,
            params=params,
            json=json,
        )
        response.raise_for_status()
        if not response.text:
            return {"success": True}
        return response.json()


_runtime_orchestrator_client: Optional[RuntimeOrchestratorClient] = None


def get_runtime_orchestrator_client() -> RuntimeOrchestratorClient:
    """Get singleton RuntimeOrchestratorClient."""
    global _runtime_orchestrator_client
    if _runtime_orchestrator_client is None:
        _runtime_orchestrator_client = RuntimeOrchestratorClient()
    return _runtime_orchestrator_client


async def close_runtime_orchestrator_client() -> None:
    """Close singleton RuntimeOrchestratorClient."""
    global _runtime_orchestrator_client
    if _runtime_orchestrator_client is not None:
        await _runtime_orchestrator_client.close()
        _runtime_orchestrator_client = None
