"""
Unified HTTP client helpers with trust_env semantics.

- Internal: service-to-service calls use ServiceConfig.INTERNAL_HTTP_TRUST_ENV
- External: LLM, MCP, web APIs use trust_env=False (bypass proxy by default)
"""

from __future__ import annotations

from typing import Any
import httpx

from common.config import ServiceConfig


def internal_async_client(**kwargs: Any) -> httpx.AsyncClient:
    """Create AsyncClient for internal service-to-service calls."""
    merged = {**kwargs, "trust_env": ServiceConfig.INTERNAL_HTTP_TRUST_ENV}
    return httpx.AsyncClient(**merged)


def internal_sync_client(**kwargs: Any) -> httpx.Client:
    """Create sync Client for internal service-to-service calls."""
    merged = {**kwargs, "trust_env": ServiceConfig.INTERNAL_HTTP_TRUST_ENV}
    return httpx.Client(**merged)


def external_async_client(**kwargs: Any) -> httpx.AsyncClient:
    """Create AsyncClient for external API calls (LLM, MCP, web). trust_env=False."""
    merged = {**kwargs, "trust_env": False}
    return httpx.AsyncClient(**merged)


def external_sync_client(**kwargs: Any) -> httpx.Client:
    """Create sync Client for external API calls. trust_env=False."""
    merged = {**kwargs, "trust_env": False}
    return httpx.Client(**merged)


# Backward-compatible aliases (used by gateway/, task_queue/, etc.)
internal_client = internal_sync_client
external_client = external_sync_client
