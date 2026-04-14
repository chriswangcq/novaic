"""
Agent VM/Mobile/HD proxy routes — extracted from gateway/api/internal/agent.py.

These routes are called by Cortex/Tools for device operations on agents:
  /internal/agents/{agent_id}/vm/{path}     — Linux VM tools
  /internal/agents/{agent_id}/mobile/{path} — Android tools
  /internal/agents/{agent_id}/hd/{path}     — Host Desktop tools
"""

import asyncio
import json
import logging

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from device.agent_binding import (
    resolve_agent_runtime_context,
    is_tool_mounted,
    is_hd_tool_mounted,
    normalize_mounted_tools,
    MOUNTED_TOOL_CATEGORIES,
    MOUNTED_TOOL_CATEGORIES_HD,
    is_mobile_tool_mounted,
)
from device.pc_client import get_pc_client_manager

logger = logging.getLogger(__name__)
_proxy_logger = logging.getLogger(__name__ + ".proxy")

router = APIRouter(tags=["internal"])

_PROXY_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


def _get_agent_devices(agent_id: str) -> tuple:
    """Get agent's device configuration (legacy fallback)."""
    from device.config_agents import get_agent_config_manager

    try:
        agent_manager = get_agent_config_manager()
        agent = agent_manager.get_agent(agent_id)
    except Exception as e:
        _proxy_logger.warning("Failed to get agent config for %s: %s", agent_id, e)
        return None, None

    if not agent:
        return None, None

    linux_device = None
    android_device = None
    for device in (getattr(agent, "devices", None) or []):
        if not isinstance(device, dict):
            continue
        if device.get("type") == "linux" and linux_device is None:
            linux_device = device
        elif device.get("type") == "android" and android_device is None:
            android_device = device
        if linux_device and android_device:
            break

    return linux_device, android_device


async def _proxy_to_vmcontrol(
    request: Request,
    target_url: str,
    agent_id: str,
    path: str,
) -> JSONResponse:
    """Generic proxy: forward request to VmControl and handle response."""
    _proxy_logger.info("Proxying %s %s for agent %s -> %s", request.method, path, agent_id, target_url)

    try:
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}

        async with httpx.AsyncClient(timeout=_PROXY_TIMEOUT) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
                params=dict(request.query_params),
            )

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                response_body = response.json()
            except Exception:
                _proxy_logger.warning("Invalid JSON from VmControl: %s", target_url)
                response_body = {"success": False, "error": "Invalid JSON response from VmControl"}
        else:
            _proxy_logger.warning("VmControl returned non-JSON (%s): %s", content_type, target_url)
            response_body = {
                "success": False,
                "error": f"VmControl returned non-JSON response (status={response.status_code})",
            }

        return JSONResponse(response_body, status_code=response.status_code)

    except httpx.ConnectError as e:
        _proxy_logger.warning("VmControl unreachable for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": "VmControl service unreachable"}, status_code=503)

    except httpx.TimeoutException as e:
        _proxy_logger.warning("VmControl timeout for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": "VmControl request timeout"}, status_code=504)

    except Exception as e:
        _proxy_logger.exception("VM proxy error for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": "Internal proxy error"}, status_code=500)


@router.api_route("/agents/{agent_id}/vm/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_vm_tool(agent_id: str, path: str, request: Request):
    """Proxy VM tool requests to VmControl via Tauri App WebSocket."""
    resolved = resolve_agent_runtime_context(None, agent_id)
    linux_device = None
    mounted_tools = []
    if resolved is not None:
        device = resolved.get("device") or {}
        if device.get("type") == "linux":
            linux_device = device
        mounted_tools = resolved.get("mounted_tools", []) or []
    else:
        linux_device, _ = _get_agent_devices(agent_id)

    if not linux_device:
        return JSONResponse({"success": False, "error": f"Agent {agent_id} has no Linux VM binding/configured device"}, status_code=404)

    parts = path.split("/", 1)
    path_family = parts[0]
    path_op = parts[1] if len(parts) > 1 else ""
    if path_family:
        if resolved is not None:
            raw_mounted = resolved.get("mounted_tools") or {}
            mounted = normalize_mounted_tools(raw_mounted, device_type="linux") if isinstance(raw_mounted, (dict, list)) else {}
        else:
            mounted = {}
        if path_op:
            allowed = is_tool_mounted(mounted, path_family, path_op)
        else:
            allowed = path_family not in MOUNTED_TOOL_CATEGORIES or bool(mounted.get(path_family))
        if not allowed:
            return JSONResponse(
                {"success": False, "error": f"Tool '{path_family}/{path_op}' is not enabled for agent {agent_id}".rstrip("/")},
                status_code=403,
            )

    manager = get_pc_client_manager()
    if not manager.is_connected:
        return JSONResponse({"success": False, "error": "No PC client connected (Tauri App not running)"}, status_code=503)

    vc_path = f"/api/vmuse/{agent_id}/{path}"
    if request.query_params:
        vc_path = f"{vc_path}?{request.query_params}"
    raw_body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}

    body = raw_body
    if raw_body:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            logger.debug("[Agent] PC proxy body is not JSON, passing raw: %s", e)
            payload = None
    else:
        payload = {}

    if isinstance(payload, dict):
        if resolved is not None:
            payload.setdefault("binding", resolved.get("binding"))
            payload.setdefault("subject", resolved.get("subject"))
            rc = resolved.get("runtime_context")
            if rc is not None:
                payload["runtime_context"] = rc
            payload.setdefault("mounted_tools", mounted_tools)
        body = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"

    _proxy_logger.info("Forwarding VM request via PC client: %s %s (agent=%s)", request.method, vc_path, agent_id)

    try:
        response = await manager.forward_request(request.method, vc_path, body, headers)
        resp_body = response.get("body")
        return JSONResponse(resp_body if resp_body is not None else {}, status_code=response.get("status", 200))
    except ConnectionError as e:
        _proxy_logger.warning("PC client unavailable for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)
    except asyncio.TimeoutError:
        _proxy_logger.warning("PC client request timeout for %s: %s", agent_id, vc_path)
        return JSONResponse({"success": False, "error": "PC client request timeout"}, status_code=504)
    except Exception as e:
        _proxy_logger.exception("PC client proxy error for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": "Internal proxy error"}, status_code=500)


@router.api_route("/agents/{agent_id}/mobile/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_mobile_tool(agent_id: str, path: str, request: Request):
    """Proxy Mobile tool requests to VmControl via Tauri App WebSocket."""
    resolved = resolve_agent_runtime_context(None, agent_id)
    if not resolved:
        return JSONResponse({"success": False, "error": f"Agent {agent_id} has no device binding"}, status_code=404)

    device = resolved.get("device") or {}
    if device.get("type") != "android":
        return JSONResponse({"success": False, "error": f"Agent {agent_id} binding is not Android device"}, status_code=404)

    device_serial = device.get("device_serial") or ""
    if not device_serial:
        return JSONResponse({"success": False, "error": f"Agent {agent_id} Android device has no serial"}, status_code=404)

    mounted = resolved.get("mounted_tools") or {}
    if isinstance(mounted, list):
        mounted = normalize_mounted_tools(mounted, device_type="android")
        return JSONResponse(
            {"success": False, "error": f"Tool '{path}' is not enabled for agent {agent_id}"},
            status_code=403,
        )

    manager = get_pc_client_manager()
    if not manager.is_connected:
        return JSONResponse({"success": False, "error": "No PC client connected (Tauri App not running)"}, status_code=503)

    vc_path = f"/api/android/{device_serial}/{path}"
    if request.query_params:
        vc_path = f"{vc_path}?{request.query_params}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}

    _proxy_logger.info("Forwarding Mobile request via PC client: %s %s (agent=%s, serial=%s)", request.method, vc_path, agent_id, device_serial)

    try:
        response = await manager.forward_request(request.method, vc_path, body, headers)
        resp_body = response.get("body")
        return JSONResponse(resp_body if resp_body is not None else {}, status_code=response.get("status", 200))
    except ConnectionError as e:
        _proxy_logger.warning("PC client unavailable for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)
    except asyncio.TimeoutError:
        _proxy_logger.warning("PC client request timeout for %s: %s", agent_id, vc_path)
        return JSONResponse({"success": False, "error": "PC client request timeout"}, status_code=504)
    except Exception as e:
        _proxy_logger.exception("PC client proxy error for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": "Internal proxy error"}, status_code=500)


@router.api_route("/agents/{agent_id}/hd/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_hd_tool(agent_id: str, path: str, request: Request):
    """Proxy Host Desktop tool requests to VmControl via Tauri App WebSocket."""
    resolved = resolve_agent_runtime_context(None, agent_id)
    if not resolved:
        return JSONResponse({"success": False, "error": f"Agent {agent_id} has no device binding"}, status_code=404)

    device = resolved.get("device") or {}
    if device.get("type") != "host_desktop":
        return JSONResponse({"success": False, "error": f"Agent {agent_id} binding is not Host Desktop device"}, status_code=404)

    parts = path.split("/", 1)
    path_family = parts[0]
    path_op = parts[1] if len(parts) > 1 else ""
    mounted = resolved.get("mounted_tools") or {}
    if isinstance(mounted, list):
        mounted = normalize_mounted_tools(mounted, device_type="host_desktop")

    if path_family:
        if path_op:
            allowed = is_hd_tool_mounted(mounted, path_family, path_op)
        else:
            allowed = path_family not in MOUNTED_TOOL_CATEGORIES_HD or bool(mounted.get(path_family))
        if not allowed:
            tool_path = f"{path_family}/{path_op}".rstrip("/")
            return JSONResponse(
                {"success": False, "error": f"Tool '{tool_path}' is not enabled for agent {agent_id}"},
                status_code=403,
            )

    manager = get_pc_client_manager()
    if not manager.is_connected:
        return JSONResponse({"success": False, "error": "No PC client connected (Tauri App not running)"}, status_code=503)

    vc_path = f"/api/hd/{path}"
    if request.query_params:
        vc_path = f"{vc_path}?{request.query_params}"
    raw_body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}

    body = raw_body
    if raw_body:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            payload = None
    else:
        payload = {}

    if isinstance(payload, dict):
        if resolved is not None:
            payload.setdefault("binding", resolved.get("binding"))
            payload.setdefault("subject", resolved.get("subject"))
            rc = resolved.get("runtime_context")
            if rc is not None:
                payload["runtime_context"] = rc
            payload.setdefault("mounted_tools", resolved.get("mounted_tools"))
        body = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"

    _proxy_logger.info("Forwarding HD request via PC client: %s %s (agent=%s)", request.method, vc_path, agent_id)

    try:
        response = await manager.forward_request(request.method, vc_path, body, headers)
        resp_body = response.get("body")
        return JSONResponse(resp_body if resp_body is not None else {}, status_code=response.get("status", 200))
    except ConnectionError as e:
        _proxy_logger.warning("PC client unavailable for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)
    except asyncio.TimeoutError:
        _proxy_logger.warning("PC client request timeout for %s: %s", agent_id, vc_path)
        return JSONResponse({"success": False, "error": "PC client request timeout"}, status_code=504)
    except Exception as e:
        _proxy_logger.exception("PC client proxy error for %s: %s", agent_id, e)
        return JSONResponse({"success": False, "error": "Internal proxy error"}, status_code=500)
