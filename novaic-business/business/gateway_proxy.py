"""
Proxy for cross-service entity actions.

Forwards action hook requests to Gateway or Device Service internal endpoints
using the same Entangled action hook protocol.
"""

import logging
from typing import Any, Dict

import httpx

from common.config import ServiceConfig

logger = logging.getLogger(__name__)

_PROXY_TIMEOUT = 30.0


def _forward_to_service(
    service_url: str,
    service_name: str,
    entity: str,
    action: str,
    store,
    user_id: str,
    params: Dict[str, str],
    data: Dict[str, Any],
) -> Any:
    """Forward an action hook request to a service's internal endpoint."""
    base = service_url.rstrip("/")
    url = f"{base}/internal/entities/{entity}/action/{action}"

    body = {
        "user_id": user_id,
        "params": params,
        "payload": data,
    }

    try:
        with httpx.Client(timeout=_PROXY_TIMEOUT) as client:
            resp = client.post(url, json=body)
            resp.raise_for_status()
            result = resp.json()
            return result.get("data", result)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        logger.error(
            "[%sProxy] %s.%s HTTP %s: %s",
            service_name, entity, action, exc.response.status_code, detail,
        )
        raise ValueError(f"{service_name} returned {exc.response.status_code}: {detail}")
    except Exception as exc:
        logger.error("[%sProxy] %s.%s failed: %s", service_name, entity, action, exc)
        raise ValueError(f"{service_name} proxy error: {exc}")


def forward_to_gateway(entity, action, store, user_id, params, data):
    return _forward_to_service(
        ServiceConfig.GATEWAY_URL, "Gateway",
        entity, action, store, user_id, params, data,
    )


def forward_to_device(entity, action, store, user_id, params, data):
    return _forward_to_service(
        ServiceConfig.DEVICE_URL, "Device",
        entity, action, store, user_id, params, data,
    )


def make_proxy_handler(entity: str, action: str):
    """Return a handler function that proxies to Gateway for this entity/action."""
    def _proxy(store, user_id, params, data):
        return forward_to_gateway(entity, action, store, user_id, params, data)
    _proxy.__name__ = f"proxy_{entity}_{action}"
    _proxy.__doc__ = f"Proxy {entity}.{action} to Gateway"
    return _proxy


def make_device_proxy_handler(entity: str, action: str):
    """Return a handler function that proxies to Device Service for this entity/action."""
    def _proxy(store, user_id, params, data):
        return forward_to_device(entity, action, store, user_id, params, data)
    _proxy.__name__ = f"proxy_device_{entity}_{action}"
    _proxy.__doc__ = f"Proxy {entity}.{action} to Device Service"
    return _proxy
