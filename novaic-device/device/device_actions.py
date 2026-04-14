"""
gateway/api/device_actions.py — Device Entity Actions.

Migrated from _dispatch_request / _dispatch_device_action in app_client.py.
All device lifecycle operations: setup, start, stop, VM, Android, WebRTC.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_device(store, user_id: str, payload: Dict[str, Any], params: Dict[str, str]):
    """Get device row from EntityStore (Entangled), check ownership."""
    from fastapi import HTTPException

    device_id = payload.get("device_id") or params.get("device_id")
    if not device_id:
        raise ValueError("device_id is required")

    row = store.get("devices", user_id, device_id)
    if row:
        from device.config_devices import device_from_dict
        device = device_from_dict(row)
        return device, device_id

    raise HTTPException(status_code=404, detail="Device not found")


def _result_to_dict(result) -> dict:
    """Convert Pydantic model or dict result to plain dict."""
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    if isinstance(result, dict):
        return result
    return {"result": str(result)}


# ── Device Lifecycle (setup / start / stop) ──────────────────────────────────

async def setup_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.setup — Initialize device (Linux disk + cloud-init, or Android AVD).

    Payload:
        device_id:      str (required)
        pc_client_id:   str (optional, multi-PC routing)
        source_image:   str (Linux disk image path)
        use_cn_mirrors: bool
    """
    from device.devices import (
        _setup_linux_device, _setup_android_device,
        SetupDeviceRequest, DeviceType,
    )

    device, device_id = _get_device(store, user_id, payload, params)
    pc_client_id = payload.get("pc_client_id")

    req = SetupDeviceRequest(
        source_image=payload.get("source_image", ""),
        use_cn_mirrors=payload.get("use_cn_mirrors", False),
    )

    if device.type == DeviceType.LINUX:
        return await _setup_linux_device(device, req, user_id, pc_client_id)
    else:
        return await _setup_android_device(device, req, user_id, pc_client_id)


async def start_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.start — Start a device (Linux VM, Android emulator, or Host Desktop).

    Payload:
        device_id:    str (required)
        pc_client_id: str (optional, multi-PC routing)
    """
    from device.devices import (
        _start_linux_device, _start_android_device, _start_host_desktop,
        ensure_device_available,
        DeviceType, DeviceStatus,
    )

    device, device_id = _get_device(store, user_id, payload, params)
    pc_client_id = payload.get("pc_client_id")

    if not (device.status == DeviceStatus.CREATED and device.type == DeviceType.ANDROID):
        ensure_device_available(device, user_id)
    if device.status == DeviceStatus.RUNNING:
        return {"status": "ok", "message": "Device already running"}

    if device.type == DeviceType.LINUX:
        return await _start_linux_device(device, user_id, pc_client_id)
    elif device.type == DeviceType.HOST_DESKTOP:
        return await _start_host_desktop(device, user_id, pc_client_id)
    else:
        return await _start_android_device(device, user_id, pc_client_id)


async def stop_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.stop — Stop a running device.

    Payload:
        device_id:    str (required)
        pc_client_id: str (optional)
    """
    from device.devices import _stop_device

    device, device_id = _get_device(store, user_id, payload, params)
    pc_client_id = payload.get("pc_client_id")

    result = await _stop_device(device, user_id, pc_client_id)
    store.update("devices", user_id, device_id, {"status": "stopped"})
    return result


# ── VM Operations ────────────────────────────────────────────────────────────

async def vm_start_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.vm_start — Start Linux VM via QEMU (agent-scoped).

    Payload:
        agent_id:     str (required)
        memory:       str (default '4096')
        cpus:         int (default 4)
        pc_client_id: str (optional)
    """
    from device.vm_routes import start_vm, VmStartRequest

    req = VmStartRequest(**payload)
    return await start_vm(req, auto_deploy_vmuse=True, user_id=user_id)


async def vm_stop_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.vm_stop — Stop Linux VM (agent-scoped).

    Payload:
        agent_id:     str (required)
        graceful:     bool (default True)
        pc_client_id: str (optional)
    """
    from device.vm_routes import stop_vm, VmStopRequest

    req = VmStopRequest(**payload)
    return await stop_vm(req, user_id=user_id)


# ── Android Operations ──────────────────────────────────────────────────────

async def android_start_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.android_start — Start Android Emulator.

    Payload:
        agent_id: str (required)
    """
    from device.vm_routes import start_android, AndroidStartRequest

    req = AndroidStartRequest(**payload)
    res = await start_android(req, user_id=user_id)
    return _result_to_dict(res)


async def android_stop_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.android_stop — Stop Android Emulator.

    Payload:
        agent_id: str (required)
    """
    from device.vm_routes import stop_android, AndroidStopRequest

    req = AndroidStopRequest(**payload)
    res = await stop_android(req, user_id=user_id)
    return _result_to_dict(res)


# ── WebRTC ───────────────────────────────────────────────────────────────────

async def webrtc_stop_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.webrtc_stop — Stop a WebRTC session by relaying to the target PC.

    Payload:
        device_id:  str (used to identify target PC)
        session_id: str
    """
    from device.pc_client import (
        get_pc_client_manager, send_push_to_device,
    )

    # Find target PC for this user
    pc_mgr = get_pc_client_manager(user_id=user_id)
    target_pc = None
    if pc_mgr:
        for client in pc_mgr.clients.values():
            target_pc = client
            break

    if target_pc is None:
        raise ValueError(f"No connected PC for user {user_id}")

    await send_push_to_device(target_pc, "webrtc_stop", payload)
    logger.info("[DeviceAction] webrtc_stop relayed to PC %s", target_pc.device_id)
    return {"success": True}


# ── Registry snapshot (WS-first; avoids nginx HTTP rate limits on /api/devices/grouped) ─

def grouped_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    devices.grouped — Same response as GET /api/devices/grouped (DeviceRegistry / PC floors).

    Params or payload:
        current_app_instance_id: optional; marks is_local for this app instance
    """
    from device.devices import compute_grouped_devices

    raw = (params.get("current_app_instance_id") or (payload or {}).get("current_app_instance_id") or "")
    cid = raw if isinstance(raw, str) else str(raw)
    return compute_grouped_devices(user_id, cid)


# ── Query Actions ────────────────────────────────────────────────────────────

async def get_status_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """devices.get_status — Get device runtime status."""
    device, device_id = _get_device(store, user_id, payload, params)
    pc_client_id = payload.get("pc_client_id") or getattr(device, "pc_client_id", None)

    pc_id = (getattr(device, "pc_client_id", None) or "").strip()
    if not pc_id:
        return {
            "device_id": device_id,
            "type": getattr(device, "type", "linux") if isinstance(getattr(device, "type", "linux"), str) else device.type.value,
            "status": getattr(device, "status", "stopped") if isinstance(getattr(device, "status", "stopped"), str) else device.status.value,
            "running": False,
        }

    from device.pc_client import get_device_registry
    registry = get_device_registry()
    dev_state = registry.get_device(pc_id)
    pc_online = dev_state is not None and dev_state.is_connected and dev_state.user_id == user_id

    dev_type = getattr(device, "type", "linux")
    dev_type_str = dev_type if isinstance(dev_type, str) else dev_type.value
    dev_status = getattr(device, "status", "stopped")
    dev_status_str = dev_status if isinstance(dev_status, str) else dev_status.value

    running = False
    if pc_online:
        try:
            from device.devices import _is_linux_device_running, _is_host_desktop_running, _is_android_device_running
            if dev_type_str == "linux":
                running = await _is_linux_device_running(device, user_id, pc_client_id)
            elif dev_type_str == "host_desktop":
                running = await _is_host_desktop_running(device, user_id, pc_client_id)
            else:
                running = await _is_android_device_running(device, user_id, pc_client_id)
        except Exception:
            logger.debug("[get_status_action] runtime probe failed for %s", device_id[:8])

    if running:
        dev_status_str = "running"
    elif dev_status_str == "running" and not running:
        dev_status_str = "ready" if pc_online else "stopped"

    return {
        "device_id": device_id,
        "type": dev_type_str,
        "status": dev_status_str,
        "running": running,
    }


def get_subjects_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """devices.get_subjects — List subjects (VM users / host desktop) of a device."""
    from device.agent_binding import list_device_subjects

    device, device_id = _get_device(store, user_id, payload, params)
    subjects = list_device_subjects(device)
    
    # Needs to match frontend DeviceSubjectsResponse expectation
    return {"subjects": subjects}


def get_tool_capabilities_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """devices.get_tool_capabilities — List tool capabilities of a device."""
    from device.agent_binding import list_device_subjects, VALID_SUBJECT_TYPES, _normalize_subject_id, get_device_subject

    device, device_id = _get_device(store, user_id, payload, params)
    subject_type = payload.get("subject_type")
    subject_id = payload.get("subject_id")

    if subject_type is None:
        all_caps = sorted({
            tool
            for subject in list_device_subjects(device)
            for tools in (subject.get("supported_tools") or {}).values()
            for tool in tools
        })
        return {
            "device_id": device_id,
            "capabilities": all_caps,
        }

    if subject_type not in VALID_SUBJECT_TYPES:
        raise ValueError(f"Invalid subject_type: {subject_type}")

    normalized_subject_id = _normalize_subject_id(subject_type, subject_id)
    if subject_type == "vm_user" and not normalized_subject_id:
        raise ValueError("subject_id is required for vm_user")

    subject = get_device_subject(device, subject_type, normalized_subject_id)
    if subject is None:
        raise ValueError("Device subject not found")

    st = subject.get("supported_tools") or {}
    caps = [t for tools in st.values() for t in tools]
    return {
        "device_id": device_id,
        "subject_type": subject_type,
        "subject_id": normalized_subject_id,
        "capabilities": caps,
    }


async def android_status_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """devices.android_status — Get Android emulator status."""
    from device.vm_routes import get_android_status

    agent_id = payload.get("agent_id") or params.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    return await get_android_status(agent_id, user_id)

