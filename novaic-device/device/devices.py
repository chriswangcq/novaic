"""
Device helper functions — setup, start, stop, status and utility helpers.

This module provides internal functions for managing devices (Linux VM, Android,
Host Desktop). The public REST endpoints have been moved to the routes layer.
"""

import asyncio
from typing import Any, Optional, Dict
from fastapi import HTTPException
import logging
from pathlib import Path

from device.entity_store import get_entity_store
from device.config_devices import (
    Device, LinuxDevice, AndroidDevice, HostDesktopDevice,
    DeviceType, DeviceStatus,
)

logger = logging.getLogger(__name__)


from device.device_models import (
    SetupDeviceRequest,
    DeviceResponse,
)


# ==================== Helper Functions ====================

def _dict_to_device(row: dict) -> Device:
    """Convert an EntityStore dict to a Device model."""
    import json as _json
    d = dict(row)
    dtype = d.get("type", "linux")
    d["type"] = DeviceType(dtype) if isinstance(dtype, str) else dtype
    status = d.get("status", "created")
    d["status"] = DeviceStatus(status) if isinstance(status, str) else status
    ports = d.get("ports") or {}
    if isinstance(ports, str):
        try:
            ports = _json.loads(ports)
        except Exception:
            ports = {}
    d["ports"] = ports
    for bool_field in ("cloud_init_complete", "managed"):
        if bool_field in d and isinstance(d[bool_field], (int, str)):
            d[bool_field] = bool(int(d[bool_field])) if d[bool_field] != "" else False
    if dtype == "android":
        return AndroidDevice(**{k: v for k, v in d.items() if k in AndroidDevice.model_fields})
    elif dtype == "host_desktop":
        return HostDesktopDevice(**{k: v for k, v in d.items() if k in HostDesktopDevice.model_fields})
    else:
        return LinuxDevice(**{k: v for k, v in d.items() if k in LinuxDevice.model_fields})


def _store_get(device_id: str, user_id: str) -> Optional[Device]:
    """Get a device from EntityStore and convert to Device model."""
    row = get_entity_store().get("devices", user_id, device_id)
    if not row:
        return None
    return _dict_to_device(row)


def _store_update(device_id: str, user_id: str, **kwargs) -> Optional[Device]:
    """Update a device via EntityStore. Converts enum values to strings."""
    data = {}
    for k, v in kwargs.items():
        if isinstance(v, DeviceStatus):
            data[k] = v.value
        elif isinstance(v, DeviceType):
            data[k] = v.value
        elif isinstance(v, dict):
            import json as _json
            data[k] = _json.dumps(v)
        else:
            data[k] = v
    result = get_entity_store().update("devices", user_id, device_id, data)
    if result:
        return _dict_to_device(result)
    return None


def _store_update_status(device_id: str, user_id: str, status: DeviceStatus) -> None:
    """Update device status via EntityStore."""
    get_entity_store().update("devices", user_id, device_id, {"status": status.value})


def _store_create(device: Device) -> None:
    """Create a device via EntityStore."""
    import json as _json
    data = device.model_dump()
    data["type"] = device.type.value
    data["status"] = device.status.value
    if isinstance(data.get("ports"), dict):
        data["ports"] = _json.dumps(data["ports"])
    for bool_field in ("cloud_init_complete", "managed"):
        if bool_field in data:
            data[bool_field] = 1 if data[bool_field] else 0
    get_entity_store().create("devices", device.user_id or "", data)


def _store_delete(device_id: str, user_id: str) -> bool:
    """Delete a device via EntityStore."""
    return get_entity_store().delete("devices", user_id, device_id)


def _check_device_owner(device_id: str, user_id: str) -> Device:
    """Load device and verify user_id ownership. Returns the device."""
    device = _store_get(device_id, user_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return device


def ensure_device_available(device_or_row, user_id: str) -> None:
    """
    P3-1: 校验设备是否可用。不可用则 raise HTTPException。
    - device.pc_client_id 为空 → 400
    - pc_client offline 或属于其他 user → 503
    device_or_row: Device 或 dict 含 pc_client_id 键。
    """
    pc_id = ""
    if hasattr(device_or_row, "pc_client_id"):
        pc_id = (getattr(device_or_row, "pc_client_id") or "").strip()
    elif isinstance(device_or_row, dict):
        pc_id = (device_or_row.get("pc_client_id") or "").strip()
    if not pc_id:
        raise HTTPException(status_code=400, detail="设备未绑定物理 PC，请先完成 setup")
    from device.pc_client import get_device_registry
    registry = get_device_registry()
    dev_state = registry.get_device(pc_id)
    if dev_state is None or not dev_state.is_connected:
        raise HTTPException(status_code=503, detail="设备当前不可用：PC 离线或未连接")
    if dev_state.user_id != user_id:
        raise HTTPException(status_code=503, detail="设备当前不可用：PC 已被其他用户占用")


def _compute_device_available(device: Device, user_id: str) -> bool:
    """
    P4-1: 计算设备 available。
    available = pc_client 在线且属于该 user 且 device 运行中。
    """
    pc_id = (getattr(device, "pc_client_id", None) or "").strip()
    if not pc_id:
        return False
    from device.pc_client import get_device_registry
    registry = get_device_registry()
    dev_state = registry.get_device(pc_id)
    if dev_state is None or not dev_state.is_connected:
        return False
    if dev_state.user_id != user_id:
        return False
    return device.status == DeviceStatus.RUNNING


def device_to_response(device: Device, user_id: Optional[str] = None) -> DeviceResponse:
    """Convert Device to response model. P4-1: 传入 user_id 时计算 available。"""
    data = device.model_dump()
    data['type'] = device.type.value
    data['status'] = device.status.value
    if user_id:
        data['available'] = _compute_device_available(device, user_id)
    return DeviceResponse(**data)


def _get_pc_manager_for_device(device, user_id: str, pc_client_id: Optional[str] = None):
    """P2-8: 获取设备操作的目标 PC manager。优先级：显式传入 > device.pc_client_id > 第一个。"""
    from device.pc_client import get_pc_client_manager
    target = (pc_client_id or "").strip() or (getattr(device, "pc_client_id", None) or "").strip()
    return get_pc_client_manager(user_id, target if target else None)


def get_data_dir() -> Path:
    """Get the data directory."""
    from common.config import ServiceConfig
    return Path(ServiceConfig.DATA_DIR)


def _normalize_subject_id(subject_type: str, subject_id: Optional[str]) -> str:
    normalized = (subject_id or "").strip()
    if subject_type == "main":
        return "main"
    if subject_type == "default":
        return "default"
    return normalized


def allocate_ports_for_device(device_type: DeviceType) -> dict:
    """Allocate ports for a new device."""
    from device.config_agents_db import BASE_PORT, BASE_VMUSE_PORT
    import json

    all_devices = get_entity_store().list("devices", "")
    used_ssh: set = set()
    used_vmuse: set = set()
    for row in all_devices:
        ports = row.get("ports") or {}
        if isinstance(ports, str):
            try:
                ports = json.loads(ports)
            except Exception:
                ports = {}
        if 'ssh' in ports:
            used_ssh.add(ports['ssh'])
        if 'vmuse' in ports:
            used_vmuse.add(ports['vmuse'])

    ssh_port = BASE_PORT
    while ssh_port in used_ssh:
        ssh_port += 1

    vmuse_port = BASE_VMUSE_PORT
    while vmuse_port in used_vmuse:
        vmuse_port += 1

    if device_type == DeviceType.LINUX:
        return {'ssh': ssh_port, 'vmuse': vmuse_port}
    else:
        return {}


def compute_grouped_devices(user_id: str, current_app_instance_id: str = "") -> Dict[str, Any]:
    """
    Build the same payload as GET /api/devices/grouped — from in-memory DeviceRegistry
    (CloudBridge WS). Used by HTTP route and WS entity action ``devices.grouped``.
    """
    from device.pc_client import get_device_registry

    registry = get_device_registry()
    current_pc_client_id = ""
    if current_app_instance_id.strip():
        dev = registry.get_device_by_app_instance_id(current_app_instance_id.strip())
        if dev:
            current_pc_client_id = dev.device_id

    result = []
    for device in registry.get_user_devices(user_id):
        device_id = device.device_id
        item = {
            "device_id": device_id,
            "pc_client_id": device_id,
            "online": device.is_connected,
        }
        if current_pc_client_id and device_id == current_pc_client_id:
            item["is_local"] = True
        if device.app_instance_id:
            item["app_instance_id"] = device.app_instance_id
        if device.machine_label:
            item["machine_label"] = device.machine_label
        result.append(item)

    by_app: Dict[str, dict] = {}
    for item in result:
        app_id = item.get("app_instance_id") or ""
        label = item.get("machine_label") or ""
        if app_id not in by_app:
            by_app[app_id] = {"app_instance_id": app_id, "machine_label": label, "devices": []}
        by_app[app_id]["devices"].append(item)
        if label and not by_app[app_id]["machine_label"]:
            by_app[app_id]["machine_label"] = label
        if item.get("is_local"):
            by_app[app_id]["is_local"] = True

    logger.info("[Devices] grouped: user=%s count=%d", user_id, len(result))
    return {"devices": result, "by_app_instance": list(by_app.values())}


def _broadcast_device_update(device_id: str, user_id: str, deleted: bool = False):
    """Notify clients that device metadata has changed.

    Entity sync notifications are handled automatically by Entangled (notify=True).
    This function only handles the VmControl Device Registry sync push.
    """

    # ── 同步推送给 VmControl Device Registry ─────────────────────────────
    if not deleted:
        try:
            import asyncio
            from device.pc_client import get_device_registry, _push_sync_devices
            registry = get_device_registry()
            loop = asyncio.get_event_loop()
            if loop.is_running():
                for pc_device in registry.get_connected_devices(user_id):
                    asyncio.ensure_future(_push_sync_devices(pc_device, user_id))
        except Exception as e:
            logger.debug(f"sync_devices push skipped (non-fatal): {e}")


# ==================== Internal Functions ====================

async def _setup_linux_device(device: LinuxDevice, request: SetupDeviceRequest, user_id: str, pc_client_id: Optional[str] = None):
    """Setup a Linux VM device — forwarded to local VmControl (which has qemu-img)."""
    from device.vm.ssh import get_ssh_key_manager

    _store_update_status(device.id, user_id, DeviceStatus.SETUP)

    try:
        mgr_ssh = get_ssh_key_manager()
        if device.user_id:
            ssh_pubkey = mgr_ssh.get_public_key(device.user_id)
        else:
            ssh_pubkey = ""

        mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)
        result = await mgr.vm_setup(device.id, {
            "source_image": request.source_image or "",
            "ssh_pubkey": ssh_pubkey,
            "use_cn_mirrors": request.use_cn_mirrors,
        })

        status_code = result.get("status", 200)
        body = result.get("body", {})
        if isinstance(status_code, int) and status_code >= 400:
            error_msg = body.get("error", f"VmControl setup returned {status_code}") if isinstance(body, dict) else str(body)
            _store_update_status(device.id, user_id, DeviceStatus.ERROR)
            raise HTTPException(status_code=500, detail=error_msg)

        disk_path = body.get("disk_path", str(Path(device.data_path) / "disk.qcow2")) if isinstance(body, dict) else str(Path(device.data_path) / "disk.qcow2")
        _store_update(device.id, user_id,
            status=DeviceStatus.READY,
            cloud_init_complete=False,
            image_path=disk_path,
            pc_client_id=mgr.pc_client_id or None,
        )
        _broadcast_device_update(device.id, user_id)
        logger.info(f"[Devices] Linux device {device.id} setup complete via VmControl (pc_client_id={mgr.pc_client_id})")
        return {"status": "ok", "message": "Linux device setup complete"}

    except ConnectionError as e:
        _store_update_status(device.id, user_id, DeviceStatus.ERROR)
        raise HTTPException(status_code=503, detail=f"VmControl (Tauri App) not connected: {e}")
    except HTTPException:
        raise
    except Exception as e:
        _store_update_status(device.id, user_id, DeviceStatus.ERROR)
        raise HTTPException(status_code=500, detail=str(e))


async def _setup_android_device(device: AndroidDevice, request: SetupDeviceRequest, user_id: str, pc_client_id: Optional[str] = None):
    """Setup an Android device."""
    if not device.managed:
        _store_update_status(device.id, user_id, DeviceStatus.READY)
        return {"status": "ok", "message": "External Android device ready"}

    _store_update_status(device.id, user_id, DeviceStatus.SETUP)

    try:
        mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)
        result = await mgr.android_avd_create({
            "name": device.avd_name,
            "device": "pixel_7",
            "memory": str(device.memory),
            "cores": device.cpus,
        })
        if result.get("status", 200) >= 400:
            raise Exception(f"AVD create failed: {result.get('body', {}).get('error', 'unknown error')}")

        _store_update(device.id, user_id, status=DeviceStatus.READY, pc_client_id=mgr.pc_client_id or None)
        _broadcast_device_update(device.id, user_id)
        return {"status": "ok", "message": "Android AVD created"}
    except ConnectionError as e:
        _store_update_status(device.id, user_id, DeviceStatus.ERROR)
        raise HTTPException(status_code=503, detail=f"VmControl (Tauri App) not connected: {e}")
    except Exception as e:
        _store_update_status(device.id, user_id, DeviceStatus.ERROR)
        raise HTTPException(status_code=500, detail=str(e))


async def _start_linux_device(device: LinuxDevice, user_id: str, pc_client_id: Optional[str] = None):
    """Start a Linux VM via CloudBridge → VmControl on local Mac."""
    ssh_port = device.ports.get('ssh', 0)
    vmuse_port = device.ports.get('vmuse', 0)

    vm_user_rows = get_entity_store().list(
        "vm-users", device.user_id or "",
        params={"device_id": device.id},
        order_by="display_num ASC",
    )
    vm_user_display_nums = [r["display_num"] for r in vm_user_rows]

    try:
        mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)
        body = {
            "memory": str(device.memory),
            "cpus": device.cpus,
            "ssh_port": ssh_port,
            "vmuse_port": vmuse_port,
            "image_path": device.image_path or "",
            "name": device.name or "",
            "vm_user_display_nums": vm_user_display_nums,
        }
        ctrl_result = await mgr.vm_start(vm_id=device.id, body=body)
        status_code = ctrl_result.get("status", 200)
        result = ctrl_result.get("body", {})

        if isinstance(status_code, int) and status_code >= 400:
            error_msg = result.get("error", f"VmControl returned {status_code}") if isinstance(result, dict) else str(result)
            logger.error(f"[Devices] vm_start failed for {device.id}: {error_msg}")
            _store_update_status(device.id, user_id, DeviceStatus.ERROR)
            raise HTTPException(status_code=500, detail=error_msg)

        _store_update_status(device.id, user_id, DeviceStatus.RUNNING)
        logger.info(f"[Devices] Linux VM {device.id} started via CloudBridge: {result}")

        return {"status": "ok", "message": "Linux VM starting via local VmControl", **(result if isinstance(result, dict) else {})}

    except ConnectionError as e:
        logger.error(f"[Devices] CloudBridge not connected: {e}")
        _store_update_status(device.id, user_id, DeviceStatus.ERROR)
        raise HTTPException(status_code=503, detail=f"CloudBridge (Tauri App) not connected: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Devices] _start_linux_device failed: {e}")
        _store_update_status(device.id, user_id, DeviceStatus.ERROR)
        raise HTTPException(status_code=500, detail=str(e))


async def _start_android_device(device: AndroidDevice, user_id: str, pc_client_id: Optional[str] = None):
    """Start an Android device."""
    try:
        mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)
        ctrl_result = await mgr.android_emulator_start({"avd": device.avd_name})
        result = ctrl_result.get("body", {})

        device_info = result.get('device', {})
        serial = device_info.get('serial', '')
        if serial:
            _store_update(device.id, user_id,
                device_serial=serial,
                status=DeviceStatus.RUNNING,
            )
            _broadcast_device_update(device.id, user_id)
        else:
            _store_update_status(device.id, user_id, DeviceStatus.RUNNING)

        return {"status": "ok", "message": "Android device started", "serial": serial, **result}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"VmControl (Tauri App) not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _stop_device(device: Device, user_id: str, pc_client_id: Optional[str] = None):
    """Stop a device."""
    mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)

    if device.type == DeviceType.LINUX:
        try:
            logger.info(f"[_stop_device] Sending vm_shutdown for agent {device.id}")
            await mgr.vm_shutdown(device.id)
            return {"status": "ok", "message": "Linux VM stop signal sent"}
        except ConnectionError as e:
            logger.warning(f"[_stop_device] CloudBridge not connected: {e}")
            raise HTTPException(status_code=503, detail=f"CloudBridge (Tauri App) not connected: {e}")
        except Exception as e:
            logger.error(f"[_stop_device] vm_shutdown failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    elif device.type == DeviceType.HOST_DESKTOP:
        try:
            await mgr.host_desktop_stop()
            return {"status": "ok", "message": "Host Desktop stopped"}
        except ConnectionError as e:
            raise HTTPException(status_code=503, detail=f"PC not connected: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        stored_serial = getattr(device, 'device_serial', '') or ''
        avd_name = getattr(device, 'avd_name', '') or ''
        serial = stored_serial

        try:
            ctrl_result = await mgr.android_devices()
            running_devices = ctrl_result.get("body", {}).get('devices', [])
            for d in running_devices:
                if stored_serial and d.get('serial') == stored_serial:
                    serial = d['serial']
                    break
                if avd_name and d.get('avd_name') == avd_name:
                    serial = d['serial']
                    break
        except ConnectionError as e:
            logger.warning(f"[_stop_device] CloudBridge not connected: {e}")
            raise HTTPException(status_code=503, detail=f"CloudBridge (Tauri App) not connected: {e}")
        except Exception as e:
            logger.warning(f"[_stop_device] Could not list android devices: {e}")

        if not serial:
            logger.warning(f"[_stop_device] No running serial found for android device {device.id} (avd={avd_name})")
            return {"status": "ok", "message": "Android device not found in running devices"}

        logger.info(f"[_stop_device] Sending android_emulator_stop serial={serial}")
        try:
            await mgr.android_emulator_stop({"serial": serial})
        except ConnectionError as e:
            logger.warning(f"[_stop_device] CloudBridge not connected: {e}")
            raise HTTPException(status_code=503, detail=f"CloudBridge (Tauri App) not connected: {e}")
        except Exception as e:
            logger.error(f"[_stop_device] android_emulator_stop failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        return {"status": "ok", "message": "Android device stopped"}


async def _is_linux_device_running(device: LinuxDevice, user_id: str, pc_client_id: Optional[str] = None) -> bool:
    """Check if Linux VM is running via CloudBridge."""
    try:
        mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)
        if not mgr.is_connected:
            return False
        ctrl_result = await mgr.vm_status(device.id)
        body = ctrl_result.get("body", {})
        status_code = ctrl_result.get("status", 200)
        if isinstance(status_code, int) and status_code == 404:
            return False
        return body.get("status") == "running" if isinstance(body, dict) else False
    except Exception:
        return False


async def _is_android_device_running(device: AndroidDevice, user_id: str, pc_client_id: Optional[str] = None) -> bool:
    """Check if Android device is running."""
    try:
        mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)
        ctrl_result = await mgr.android_devices()
        devices = ctrl_result.get("body", {}).get('devices', [])
        for d in devices:
            if device.device_serial and d.get('serial') == device.device_serial:
                return d.get('status') in ['device', 'connected']
            if device.avd_name and d.get('avd_name') == device.avd_name:
                return d.get('status') in ['device', 'connected']
    except Exception as e:
        logger.debug("[Devices] Android device status check failed: %s", e)
    return False


async def _delete_avd(avd_name: str, user_id: Optional[str] = None, pc_client_id: Optional[str] = None):
    """Delete an AVD via CloudBridge. P2-8: 多 PC 时指定 pc_client_id 路由到目标物理机。"""
    from device.pc_client import get_pc_client_manager
    mgr = get_pc_client_manager(user_id=user_id, pc_client_id=pc_client_id)
    await mgr.android_avd_delete(avd_name)


async def _start_host_desktop(device: Device, user_id: str, pc_client_id: Optional[str] = None):
    """Start Host Desktop RFB server via CloudBridge → PC Client."""
    try:
        mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)
        result = await mgr.host_desktop_start()
        body = result.get("body", {})
        status_code = result.get("status", 200)
        if isinstance(status_code, int) and status_code >= 400:
            error_msg = body.get("error", f"Host Desktop start returned {status_code}") if isinstance(body, dict) else str(body)
            raise HTTPException(status_code=500, detail=error_msg)
        _store_update_status(device.id, user_id, DeviceStatus.RUNNING)
        return {"status": "ok", "message": "Host Desktop started"}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC not connected: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _is_host_desktop_running(device: Device, user_id: str, pc_client_id: Optional[str] = None) -> bool:
    """Check if Host Desktop is running via CloudBridge."""
    try:
        mgr = _get_pc_manager_for_device(device, user_id, pc_client_id)
        if not mgr.is_connected:
            return False
        result = await mgr.host_desktop_status()
        body = result.get("body", {})
        return body.get("running", False) if isinstance(body, dict) else False
    except Exception:
        return False
