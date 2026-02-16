"""
HTTP client helpers with unified trust_env behavior.

- internal_* : Service-to-service calls (trust_env from ServiceConfig.INTERNAL_HTTP_TRUST_ENV)
- external_* : External API calls (LLM, MCP, etc.) - trust_env=False by default
"""

from .clients import (
    internal_async_client,
    internal_sync_client,
    external_async_client,
    external_sync_client,
    internal_client,
    external_client,
)

__all__ = [
    "internal_async_client",
    "internal_sync_client",
    "external_async_client",
    "external_sync_client",
    "internal_client",
    "external_client",
]
