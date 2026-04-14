"""
HTTP client for calling Device Service.

Gateway NEVER imports device.* Python modules directly.
All device-domain queries go through this HTTP client → Device Service (:19993).
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from common.config import ServiceConfig

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


def _device_url() -> str:
    return getattr(ServiceConfig, "DEVICE_URL", "http://127.0.0.1:19993").rstrip("/")


# ── Device Registry ──────────────────────────────────────────────────────────

def get_connected_devices(user_id: str) -> List[Dict[str, Any]]:
    """Get connected device states for a user from Device Service registry."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.get(f"{_device_url()}/internal/device-registry/connected", params={"user_id": user_id})
            r.raise_for_status()
            return r.json().get("devices", [])
    except Exception as e:
        logger.warning("[DeviceClient] get_connected_devices failed: %s", e)
        return []


def get_device_state(device_id: str) -> Optional[Dict[str, Any]]:
    """Get a device's state from Device Service in-memory registry."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.get(f"{_device_url()}/internal/device-registry/device/{device_id}")
            r.raise_for_status()
            data = r.json()
            return data if data.get("found") else None
    except Exception as e:
        logger.warning("[DeviceClient] get_device_state(%s) failed: %s", device_id, e)
        return None


async def send_push_to_device(device_id: str, msg_type: str, payload: dict) -> bool:
    """Send a push message to a connected device via Device Service."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.post(
                f"{_device_url()}/internal/device-registry/push-to-device",
                json={"device_id": device_id, "msg_type": msg_type, "payload": payload},
            )
            r.raise_for_status()
            return True
    except Exception as e:
        logger.warning("[DeviceClient] send_push_to_device(%s) failed: %s", device_id, e)
        return False


# ── Agent binding resolution ─────────────────────────────────────────────────

def resolve_agent_runtime_context(agent_id: str) -> Optional[Dict[str, Any]]:
    """Resolve agent's device binding, mounted tools, and subject via Device Service."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.get(f"{_device_url()}/internal/resolve-binding/{agent_id}")
            r.raise_for_status()
            data = r.json()
            if not data.get("resolved"):
                return None
            data.pop("resolved", None)
            return data
    except Exception as e:
        logger.warning("[DeviceClient] resolve_agent_runtime_context(%s) failed: %s", agent_id, e)
        return None


def get_available_tools_for_agent(agent_id: str) -> Dict[str, Any]:
    """Get resolved binding + tool mount mapping for agent tool filtering."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.get(f"{_device_url()}/internal/resolve-binding/{agent_id}/available-tools")
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning("[DeviceClient] get_available_tools(%s) failed: %s", agent_id, e)
        return {"resolved": False, "device_type": None, "mounted": {}, "tool_name_to_mounted": {}, "mounted_tool_categories_hd": {}}


def normalize_mounted_tools(mounted_tools: Any, *, device_type: Optional[str] = None) -> Dict[str, List[str]]:
    """Normalize mounted_tools via Device Service."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.post(
                f"{_device_url()}/internal/resolve-binding/normalize-mounted-tools",
                json={"mounted_tools": mounted_tools, "device_type": device_type},
            )
            r.raise_for_status()
            return r.json().get("mounted_tools", {})
    except Exception as e:
        logger.warning("[DeviceClient] normalize_mounted_tools failed: %s", e)
        return {}


# ── VmControl health ─────────────────────────────────────────────────────────

async def vmcontrol_healthy() -> bool:
    """Check if VmControl is healthy via Device Service."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.get(f"{_device_url()}/internal/vmcontrol-health")
            r.raise_for_status()
            return r.json().get("healthy", False)
    except Exception as e:
        logger.warning("[DeviceClient] vmcontrol_health failed: %s", e)
        return False


# ── QEMU proxy (Gateway → Device Service) ────────────────────────────────────
# These were formerly handled locally in Gateway with get_pc_client_manager().
# Now Gateway proxies to Device Service which owns the PC bridge connection.

async def proxy_qemu_request(method: str, path: str, body: Any = None) -> Dict[str, Any]:
    """Proxy a QEMU request to Device Service's /internal/agents/... endpoint."""
    url = f"{_device_url()}/internal{path}"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(130.0, connect=5.0)) as c:
            r = await c.request(method, url, json=body if body else None)
            return r.json()
    except Exception as e:
        logger.warning("[DeviceClient] proxy_qemu %s %s failed: %s", method, path, e)
        return {"success": False, "error": str(e)}
