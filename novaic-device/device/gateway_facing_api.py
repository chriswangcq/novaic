"""
HTTP APIs exposed by Device Service for Gateway to call.

Gateway should NEVER import device.* Python modules directly.
Instead, Gateway calls these HTTP endpoints when it needs device-domain info.

Endpoints:
  GET  /internal/device-registry/connected?user_id=...   → list connected devices
  GET  /internal/device-registry/device/{device_id}      → get device state
  POST /internal/device-registry/push-to-device           → send push msg to device
  GET  /internal/resolve-binding/{agent_id}               → resolve agent runtime context
  POST /internal/resolve-binding/normalize-mounted-tools  → normalize mounted_tools
  GET  /internal/resolve-binding/{agent_id}/available-tools → get available tools for agent
  GET  /internal/vmcontrol-health                         → check if VmControl is healthy
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])


# ── Device Registry queries ──────────────────────────────────────────────────

@router.get("/device-registry/connected")
async def list_connected_devices(user_id: str = ""):
    """Return connected device states for a user."""
    from device.pc_client import get_device_registry
    registry = get_device_registry()
    devices = registry.get_connected_devices(user_id)
    return {
        "devices": [
            {
                "device_id": d.device_id,
                "user_id": d.user_id,
                "is_connected": d.is_connected,
                "app_instance_id": d.app_instance_id,
                "machine_label": d.machine_label,
            }
            for d in devices
        ]
    }


@router.get("/device-registry/device/{device_id}")
async def get_device_state(device_id: str):
    """Get a single device's state from the in-memory registry."""
    from device.pc_client import get_device_registry
    registry = get_device_registry()
    dev = registry.get_device(device_id)
    if dev is None:
        return {"found": False}
    return {
        "found": True,
        "device_id": dev.device_id,
        "user_id": dev.user_id,
        "is_connected": dev.is_connected,
        "app_instance_id": dev.app_instance_id,
        "machine_label": dev.machine_label,
    }


class PushToDeviceRequest(BaseModel):
    device_id: str
    msg_type: str
    payload: dict = {}


@router.post("/device-registry/push-to-device")
async def push_to_device(req: PushToDeviceRequest):
    """Send a push message to a connected device via PC bridge WS."""
    from device.pc_client import get_device_registry, send_push_to_device
    registry = get_device_registry()
    dev = registry.get_device(req.device_id)
    if dev is None or not dev.is_connected:
        raise HTTPException(status_code=404, detail="Device not connected")
    await send_push_to_device(dev, req.msg_type, req.payload)
    return {"success": True}


# ── Agent binding resolution ─────────────────────────────────────────────────

@router.get("/resolve-binding/{agent_id}")
async def resolve_binding(agent_id: str):
    """Resolve agent runtime context (device binding, mounted tools, subject)."""
    from device.agent_binding import resolve_agent_runtime_context
    resolved = resolve_agent_runtime_context(None, agent_id)
    if resolved is None:
        return {"resolved": False}
    return {"resolved": True, **resolved}


class NormalizeMountedToolsRequest(BaseModel):
    mounted_tools: Any
    device_type: Optional[str] = None


@router.post("/resolve-binding/normalize-mounted-tools")
async def normalize_mounted_tools_api(req: NormalizeMountedToolsRequest):
    from device.agent_binding import normalize_mounted_tools
    result = normalize_mounted_tools(req.mounted_tools, device_type=req.device_type)
    return {"mounted_tools": result}


@router.get("/resolve-binding/{agent_id}/available-tools")
async def get_available_tools_for_agent(agent_id: str):
    """Return resolved binding + TOOL_NAME_TO_MOUNTED data for an agent.

    Gateway uses this to filter which tools a subagent can access.
    """
    from device.agent_binding import (
        resolve_agent_runtime_context,
        normalize_mounted_tools,
        TOOL_NAME_TO_MOUNTED,
        MOUNTED_TOOL_CATEGORIES_HD,
        list_supported_mounted_tools,
        get_device_subject,
    )

    resolved = resolve_agent_runtime_context(None, agent_id)
    device_type = None
    mounted = {}
    if resolved is not None:
        device = resolved.get("device") or {}
        device_type = device.get("type")
        if device_type:
            device_type = device_type.split(".")[-1]
        raw_mounted = resolved.get("mounted_tools") or {}
        mounted = normalize_mounted_tools(raw_mounted, device_type=device_type)

    return {
        "resolved": resolved is not None,
        "device_type": device_type,
        "mounted": mounted,
        "tool_name_to_mounted": {k: list(v) for k, v in TOOL_NAME_TO_MOUNTED.items()},
        "mounted_tool_categories_hd": {k: list(v) for k, v in MOUNTED_TOOL_CATEGORIES_HD.items()},
    }


# ── VmControl health ─────────────────────────────────────────────────────────

@router.get("/vmcontrol-health")
async def vmcontrol_health():
    """Check if VmControl (via PC bridge) is healthy."""
    from device.pc_client import get_pc_client_manager
    try:
        healthy = await get_pc_client_manager().vm_health()
        return {"healthy": healthy}
    except Exception as e:
        logger.warning("vmcontrol health check failed: %s", e)
        return {"healthy": False}


# ── QEMU endpoints (moved from gateway/api/internal/agent.py) ────────────────

@router.get("/agents/{agent_id}/qemu/status")
async def qemu_status(agent_id: str):
    from device.pc_client import get_pc_client_manager
    try:
        manager = get_pc_client_manager()
        result = await manager.vm_status(agent_id)
        body = result.get("body", {})
        if result.get("status") == 404:
            return {"success": True, "status": "not_found", "running": False}
        return {
            "success": True,
            "status": body.get("status", "unknown"),
            "running": body.get("status") == "running",
            "vm_id": agent_id,
            "details": body,
        }
    except ConnectionError:
        return {"success": False, "error": "PC client not connected"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/agents/{agent_id}/qemu/ssh-exec")
async def qemu_ssh_exec(agent_id: str, data: Dict[str, Any]):
    from device.pc_client import get_pc_client_manager
    import json as _json

    command = data.get("command", "")
    timeout = data.get("timeout", 30)

    if not command:
        return {"success": False, "error": "command is required"}

    try:
        manager = get_pc_client_manager()
        if not manager.is_connected:
            return {"success": False, "error": "PC client (CloudBridge) not connected"}

        body = _json.dumps({"command": command, "timeout": timeout}).encode()
        result = await manager.forward_request(
            "POST",
            f"/api/vms/{agent_id}/ssh-exec",
            body,
            {"content-type": "application/json"},
            timeout=float(timeout) + 10.0,
        )

        status = result.get("status", 500)
        resp_body = result.get("body", {})

        if status >= 400:
            error = resp_body.get("error", "Unknown error") if isinstance(resp_body, dict) else str(resp_body)
            return {"success": False, "error": error}

        return resp_body

    except ConnectionError as e:
        return {"success": False, "error": f"CloudBridge connection error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/agents/{agent_id}/qemu/start")
async def qemu_start(agent_id: str, data: Dict[str, Any]):
    from device.pc_client import get_pc_client_manager
    try:
        manager = get_pc_client_manager()
        result = await manager.vm_start(agent_id, body=data if data else None)
        body = result.get("body", {})
        if result.get("status", 200) >= 400:
            return {"success": False, "error": body.get("error", f"VmControl error: {result.get('status')}")}
        return {"success": True, **body}
    except ConnectionError:
        return {"success": False, "error": "PC client not connected"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/agents/{agent_id}/qemu/shutdown")
async def qemu_shutdown(agent_id: str, data: Dict[str, Any]):
    from device.pc_client import get_pc_client_manager
    try:
        manager = get_pc_client_manager()
        result = await manager.vm_shutdown(agent_id, body=data if data else None)
        body = result.get("body", {})
        if result.get("status", 200) >= 400:
            return {"success": False, "error": body.get("error", f"VmControl error: {result.get('status')}")}
        return {"success": True, **body}
    except ConnectionError:
        return {"success": False, "error": "PC client not connected"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/agents/{agent_id}/qemu/restart")
async def qemu_restart(agent_id: str, data: Dict[str, Any]):
    from device.pc_client import get_pc_client_manager
    try:
        manager = get_pc_client_manager()
        result = await manager.vm_restart(agent_id, body=data if data else None)
        body = result.get("body", {})
        if result.get("status", 200) >= 400:
            return {"success": False, "error": body.get("error", f"VmControl error: {result.get('status')}")}
        return {"success": True, **body}
    except ConnectionError:
        return {"success": False, "error": "PC client not connected"}
    except Exception as e:
        return {"success": False, "error": str(e)}
