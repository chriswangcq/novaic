"""
PC Client WebSocket Manager — Device Registry

Tauri App（PC 端）通过此 WebSocket 端点连接到 Gateway。
当 Tools Server 需要调用 VmControl 时，Gateway 通过此连接把请求转发给 Tauri App，
Tauri App 在本地调用内嵌的 VmControl 并将结果返回。

Phase 1 改造：
  - 从全局单例 PcClientManager → 以 device_id 为键的 DeviceRegistry
  - 同一 device_id 重连时：继承状态，迁移 WS，不踢 pending
  - 不同 device_id 的设备并行共存，互不影响
  - 兼容旧调用方：get_pc_client_manager() 通过适配器保持原有接口
"""
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])


# ─── DeviceState ──────────────────────────────────────────────────────────────

@dataclass
class DeviceState:
    """单台 PC 设备的连接状态与 pending 请求表。"""
    device_id: str
    user_id: str
    ws: Optional[WebSocket] = None
    online: bool = False                       # 是否开放 Agent 控制
    vm_ids: Set[str] = field(default_factory=set)
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    app_instance_id: str = ""                  # AppInstance 唯一 ID（x-app-instance-id）
    machine_label: str = ""                    # 机器型号/主机名（x-machine-label）
    _pending: Dict[str, asyncio.Future] = field(default_factory=dict)
    _push_ack_pending: Dict[str, asyncio.Future] = field(default_factory=dict)  # R1/R5: push_id -> Future
    _send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def is_connected(self) -> bool:
        return self.ws is not None


# ─── DeviceRegistry ───────────────────────────────────────────────────────────

class DeviceRegistry:
    """
    管理所有已连接设备的 WebSocket 连接，以 device_id 为索引键。

    特性：
      - 同一 device_id 重连时继承历史状态（vm_ids、online），不踢 pending
      - 不同 device_id 的设备并行共存
      - disconnect 只置空 ws，DeviceState 保留（供下次重连恢复）
    """

    def __init__(self):
        self._devices: Dict[str, DeviceState] = {}
        self._registry_lock = asyncio.Lock()

    async def connect(
        self,
        ws: WebSocket,
        device_id: str,
        user_id: str,
        *,
        app_instance_id: str = "",
        machine_label: str = "",
    ) -> DeviceState:
        """
        注册或更新设备连接。
        同一 device_id 重连：迁移 ws，继承 vm_ids 等状态。
        不同 device_id：创建新条目。
        """
        async with self._registry_lock:
            if device_id in self._devices:
                device = self._devices[device_id]
                if device.user_id != user_id:
                    # CR R3: 若旧连接已断开(ws=None)，允许新用户接管
                    if device.ws is not None:
                        logger.warning(
                            "[DeviceRegistry] device_id %s user_id mismatch: "
                            "existing=%s, new=%s — rejecting",
                            device_id, device.user_id, user_id,
                        )
                        raise ValueError(
                            f"device_id {device_id} already registered to a different user"
                        )
                    logger.info("[DeviceRegistry] Evicting stale entry for %s (user %s → %s)", device_id, device.user_id, user_id)
                    del self._devices[device_id]
                else:
                    # 同 device_id 重连：关闭旧 WS，继承其余状态，更新 app_instance_id/machine_label
                    async with device._lock:
                        if device.ws is not None:
                            try:
                                await device.ws.close(1001, "Device reconnected")
                            except Exception as e:
                                logger.debug("[DeviceRegistry] WS close during reconnect: %s", e)
                        device.ws = ws
                        device.connected_at = datetime.utcnow()
                        device.last_seen = datetime.utcnow()
                        if app_instance_id:
                            device.app_instance_id = app_instance_id
                        if machine_label:
                            device.machine_label = machine_label
                    logger.info("[DeviceRegistry] Device %s reconnected (user=%s)", device_id, user_id)
                    return device
            # device_id 不在 _devices（新建或 evict 后）
            device = DeviceState(
                device_id=device_id,
                user_id=user_id,
                ws=ws,
                connected_at=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                app_instance_id=app_instance_id,
                machine_label=machine_label,
            )
            self._devices[device_id] = device
            logger.info(
                "[DeviceRegistry] New device %s registered (user=%s, label=%s)",
                device_id, user_id, machine_label or "(none)",
            )
            return device

    async def disconnect(self, ws: WebSocket, device_id: str) -> None:
        """
        设备断开：置空 ws，保留 DeviceState（vm_ids 等状态保留，供下次重连恢复）。
        只有当 device.ws 与传入 ws 一致时才处理（防止热重连时覆盖新连接）。
        """
        async with self._registry_lock:
            device = self._devices.get(device_id)
            if device is None:
                return
            async with device._lock:
                if device.ws is not ws:
                    return  # 已是新连接，不覆盖
                device.ws = None
                device.last_seen = datetime.utcnow()
                # 通知所有 pending futures 连接已断
                for fut in list(device._pending.values()):
                    if not fut.done():
                        fut.set_exception(ConnectionError("Device disconnected"))
                device._pending.clear()
                for fut in list(device._push_ack_pending.values()):
                    if not fut.done():
                        fut.set_exception(ConnectionError("Device disconnected"))
                device._push_ack_pending.clear()

        logger.info("[DeviceRegistry] Device %s disconnected", device_id)

    def get_device(self, device_id: str) -> Optional[DeviceState]:
        return self._devices.get(device_id)

    def get_device_by_app_instance_id(self, app_instance_id: str) -> Optional[DeviceState]:
        """Phase 2: 根据 app_instance_id 查找对应的 pc_client（Cloud Bridge 上报时关联）。"""
        if not app_instance_id or not app_instance_id.strip():
            return None
        aid = app_instance_id.strip()
        for d in self._devices.values():
            if d.app_instance_id == aid and d.is_connected:
                return d
        return None

    def get_user_devices(self, user_id: str) -> List[DeviceState]:
        """返回指定用户的所有设备（含离线）。"""
        return [d for d in self._devices.values() if d.user_id == user_id]

    def get_connected_devices(self, user_id: str) -> List[DeviceState]:
        """返回指定用户当前在线的设备。"""
        return [d for d in self._devices.values()
                if d.user_id == user_id and d.is_connected]


# ─── 全局注册表 ────────────────────────────────────────────────────────────────

_registry = DeviceRegistry()


def get_device_registry() -> DeviceRegistry:
    return _registry


# ─── forward_to_device ────────────────────────────────────────────────────────

async def forward_to_device(
    device: DeviceState,
    method: str,
    path: str,
    body: bytes,
    headers: dict,
    timeout: float = 120.0,
) -> dict:
    """
    向指定设备转发 HTTP 请求并等待 proxy_response。
    返回包含 'status' 和 'body' 的 dict。
    Raises ConnectionError 若设备未连接或发送失败。
    Raises asyncio.TimeoutError 若超时。
    """
    ws = device.ws
    if ws is None:
        raise ConnectionError(f"Device {device.device_id} not connected")

    request_id = str(uuid.uuid4())
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    async with device._lock:
        device._pending[request_id] = fut

    try:
        try:
            body_data = json.loads(body) if body else None
        except Exception:
            body_data = body.decode("utf-8", errors="replace") if body else None

        filtered_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in ("host", "content-length", "transfer-encoding")
        }
        message = {
            "type": "proxy_request",
            "id": request_id,
            "method": method,
            "path": path,
            "body": body_data,
            "headers": filtered_headers,
        }
        try:
            async with device._send_lock:
                await ws.send_json(message)
        except Exception as e:
            if not fut.done():
                fut.cancel()
            raise ConnectionError(
                f"Failed to send to device {device.device_id}: {e}"
            ) from e

        logger.debug("[PcClient] Forwarded %s %s to device %s (id=%s)",
                     method, path, device.device_id, request_id)
        return await asyncio.wait_for(fut, timeout=timeout)

    finally:
        async with device._lock:
            device._pending.pop(request_id, None)


async def send_push_to_device(
    device: DeviceState,
    msg_type: str,
    payload: dict,
) -> None:
    """
    向设备发送单向推送消息，不等待响应。
    用于 connect_relay 等通知类消息。
    """
    ws = device.ws
    if ws is None:
        raise ConnectionError(f"Device {device.device_id} not connected")

    message = {"type": msg_type, **payload}
    async with device._send_lock:
        await ws.send_json(message)
    logger.debug("[PcClient] Pushed %s to device %s", msg_type, device.device_id)


async def send_push_and_wait_ack(
    device: DeviceState,
    push_id: str,
    msg_type: str,
    payload: dict,
    timeout: float = 5.0,
) -> None:
    """
    R1/R5: 向设备发送推送并等待 ACK 回执。
    超时返回 asyncio.TimeoutError。
    """
    from common.config import ServiceConfig
    if not ServiceConfig.P2P_PUSH_ACK_ENABLED:
        await send_push_to_device(device, msg_type, payload)
        return

    ws = device.ws
    if ws is None:
        raise ConnectionError(f"Device {device.device_id} not connected")

    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    async with device._lock:
        device._push_ack_pending[push_id] = fut

    try:
        message = {"type": msg_type, "push_id": push_id, **payload}
        async with device._send_lock:
            await ws.send_json(message)
        await asyncio.wait_for(fut, timeout=timeout)
    finally:
        async with device._lock:
            device._push_ack_pending.pop(push_id, None)


async def send_control_to_device(
    device: DeviceState,
    msg_type: str,
    payload: dict,
    timeout: float = 60.0,
) -> dict:
    """
    向设备发送结构化控制消息并等待 proxy_response。
    Returns {'status': int, 'body': dict}.
    """
    ws = device.ws
    if ws is None:
        raise ConnectionError(f"Device {device.device_id} not connected")

    request_id = str(uuid.uuid4())
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    async with device._lock:
        device._pending[request_id] = fut

    message = {"type": msg_type, "id": request_id, **payload}
    try:
        async with device._send_lock:
            await ws.send_json(message)
    except Exception as e:
        if not fut.done():
            fut.cancel()
        raise ConnectionError(f"Failed to send to device {device.device_id}: {e}") from e

    try:
        response = await asyncio.wait_for(fut, timeout=timeout)
        return {"status": response.get("status", 200), "body": response.get("body", {})}
    finally:
        async with device._lock:
            device._pending.pop(request_id, None)


# ─── 兼容适配器（过渡期）─────────────────────────────────────────────────────

class _DeviceManagerAdapter:
    """
    将 DeviceState 包装为原有 PcClientManager 兼容接口。
    过渡期使用：旧调用方（vm.py 等）无需修改即可继续工作。
    """

    def __init__(self, device: DeviceState):
        self._device = device

    @property
    def is_connected(self) -> bool:
        return self._device.is_connected

    @property
    def pc_client_id(self) -> str:
        """P2-7: 物理 PC 标识，供 setup 后存储到 device 记录。"""
        return self._device.device_id

    async def forward_request(self, method, path, body, headers, timeout=120.0):
        return await forward_to_device(self._device, method, path, body, headers, timeout)

    async def send_control(self, msg_type, payload, timeout=60.0):
        return await send_control_to_device(self._device, msg_type, payload, timeout)

    # ── VM lifecycle ──────────────────────────────────────────────────────────
    async def vm_status(self, vm_id: str) -> dict:
        return await self.send_control("vm_status", {"vm_id": vm_id}, timeout=10.0)

    async def vm_setup(self, vm_id: str, body: dict) -> dict:
        """Forward VM setup (disk creation + cloud-init) to the local VmControl."""
        import json
        return await self.forward_request(
            "POST", f"/api/vms/{vm_id}/setup",
            json.dumps(body).encode(), {"Content-Type": "application/json"},
            timeout=300.0,  # disk conversion can take a few minutes
        )

    async def vm_start(self, vm_id: str, body: dict = None) -> dict:
        return await self.send_control(
            "vm_start", {"vm_id": vm_id, **({"body": body} if body else {})}, timeout=60.0
        )

    async def vm_shutdown(self, vm_id: str, body: dict = None) -> dict:
        return await self.send_control(
            "vm_shutdown", {"vm_id": vm_id, **({"body": body} if body else {})}, timeout=60.0
        )

    async def vm_delete(self, vm_id: str) -> dict:
        """Shutdown VM then delete its disk image and data directory on the PC Client."""
        try:
            await self.vm_shutdown(vm_id)
        except Exception:
            pass
        return await self.forward_request(
            "DELETE", f"/api/vms/{vm_id}", b"", {}, timeout=60.0
        )

    async def vm_restart(self, vm_id: str, body: dict = None) -> dict:
        return await self.send_control(
            "vm_restart", {"vm_id": vm_id, **({"body": body} if body else {})}, timeout=120.0
        )

    # ── Android ───────────────────────────────────────────────────────────────
    async def android_devices(self) -> dict:
        return await self.send_control("android_devices", {}, timeout=15.0)

    async def android_avds(self) -> dict:
        return await self.send_control("android_avds", {}, timeout=15.0)

    async def android_avd_create(self, body: dict) -> dict:
        return await self.send_control("android_avd_create", {"body": body}, timeout=120.0)

    async def android_avd_delete(self, avd_name: str) -> dict:
        return await self.send_control("android_avd_delete", {"avd_name": avd_name}, timeout=30.0)

    async def android_emulator_start(self, body: dict) -> dict:
        return await self.send_control("android_emulator_start", {"body": body}, timeout=180.0)

    async def android_emulator_stop(self, body: dict) -> dict:
        return await self.send_control("android_emulator_stop", {"body": body}, timeout=30.0)

    async def android_system_image_check(self) -> dict:
        return await self.send_control("android_system_image_check", {}, timeout=15.0)

    async def android_device_definitions(self) -> dict:
        return await self.send_control("android_device_definitions", {}, timeout=15.0)

    async def android_scrcpy_status(self) -> dict:
        return await self.send_control("android_scrcpy_status", {}, timeout=15.0)

    # ── VM Users (multi-user TigerVNC) ───────────────────────────────────────
    async def create_vm_user(self, vm_id: str, body: dict) -> dict:
        """Create a Linux user inside the VM and start their Xvnc session.
        Timeout is 300s to allow TigerVNC apt-get install on first use."""
        return await self.forward_request(
            "POST", f"/api/vms/{vm_id}/users",
            json.dumps(body).encode(), {"Content-Type": "application/json"},
            timeout=300.0,
        )

    async def delete_vm_user(self, vm_id: str, username: str) -> dict:
        """Stop Xvnc session and remove the Linux user from the VM."""
        return await self.forward_request(
            "DELETE", f"/api/vms/{vm_id}/users/{username}",
            b"", {}, timeout=30.0,
        )

    async def restart_vm_user_vnc(self, vm_id: str, username: str, display_num: int = None) -> dict:
        """Restart TigerVNC session for a VM user (installs TigerVNC if missing).
        display_num is passed so VmControl can add hostfwd for the VNC port (needed after VM restart)."""
        body = json.dumps({"display_num": display_num}).encode() if display_num is not None else b""
        headers = {"Content-Type": "application/json"} if body else {}
        return await self.forward_request(
            "POST", f"/api/vms/{vm_id}/users/{username}/restart",
            body, headers, timeout=300.0,
        )

    async def sync_vm_vmuse(self, vm_id: str) -> dict:
        """Hot-sync bundled vmuse code into a running VM and restart the service."""
        return await self.forward_request(
            "POST", f"/api/vms/{vm_id}/vmuse/sync",
            b"", {}, timeout=300.0,
        )

    # ── VM list / register / shutdown-all / health ────────────────────────────
    async def vm_list(self) -> dict:
        return await self.forward_request("GET", "/api/vms", b"", {}, timeout=15.0)

    async def vm_register(self, vm_id: str, name: str, qmp_socket: str) -> dict:
        body = json.dumps({"id": vm_id, "name": name, "qmp_socket": qmp_socket}).encode()
        return await self.forward_request(
            "POST", "/api/vms", body, {"content-type": "application/json"}, timeout=30.0
        )

    async def vm_shutdown_all(self) -> dict:
        return await self.forward_request("POST", "/api/vms/shutdown-all", b"", {}, timeout=60.0)

    async def vm_health(self) -> bool:
        if not self.is_connected:
            return False
        try:
            result = await self.forward_request("GET", "/health", b"", {}, timeout=5.0)
            return result.get("status", 503) == 200
        except Exception:
            return False

    # ── Host Desktop ────────────────────────────────────────────────────────────
    async def host_desktop_start(self) -> dict:
        return await self.send_control("host_desktop_start", {}, timeout=15.0)

    async def host_desktop_stop(self) -> dict:
        return await self.send_control("host_desktop_stop", {}, timeout=10.0)

    async def host_desktop_status(self) -> dict:
        return await self.send_control("host_desktop_status", {}, timeout=5.0)


class _DisconnectedAdapter:
    """无设备连接时的空实现，所有调用均返回 ConnectionError。"""
    is_connected = False
    pc_client_id = ""

    async def forward_request(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def send_control(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def vm_status(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def vm_start(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def vm_shutdown(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def vm_restart(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_devices(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_avds(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_avd_create(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_avd_delete(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_emulator_start(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_emulator_stop(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_system_image_check(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_device_definitions(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def android_scrcpy_status(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def vm_list(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def vm_register(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def vm_shutdown_all(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def vm_health(self) -> bool:
        return False

    async def host_desktop_start(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def host_desktop_stop(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def host_desktop_status(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")


# ─── 兼容接口 ─────────────────────────────────────────────────────────────────

def get_pc_client_manager(user_id: Optional[str] = None, pc_client_id: Optional[str] = None):
    """
    过渡期兼容接口，返回 PcClientManager 兼容对象。
    新代码请直接使用 get_device_registry()。

    行为：
      - pc_client_id 非空：返回该 PC 的 adapter（需属于 user_id 或 user_id 为空）
      - user_id=None：返回任意已连接设备（旧全局单例语义）
      - user_id=xxx：返回该用户的第一台已连接设备
    """
    target_id = (pc_client_id or "").strip()
    if target_id:
        device = _registry.get_device(target_id)
        if device and device.is_connected:
            if user_id is None or device.user_id == user_id:
                return _DeviceManagerAdapter(device)
        return _DisconnectedAdapter()

    if user_id is None:
        for device in _registry._devices.values():
            if device.is_connected:
                return _DeviceManagerAdapter(device)
        return _DisconnectedAdapter()

    devices = _registry.get_connected_devices(user_id)
    if devices:
        return _DeviceManagerAdapter(devices[0])
    return _DisconnectedAdapter()


# ─── WebSocket 消息处理 ────────────────────────────────────────────────────────

async def _handle_device_message(device: DeviceState, data: dict) -> None:
    """处理来自设备的消息（proxy_response / ping / vm_status_report）。"""
    msg_type = data.get("type")

    if msg_type == "proxy_response":
        request_id = data.get("id")
        fut = device._pending.get(request_id)
        if fut and not fut.done():
            fut.set_result(data)

    elif msg_type == "ping":
        if device.ws is not None:
            try:
                async with device._send_lock:
                    await device.ws.send_json({"type": "pong"})
            except Exception as e:
                logger.debug("[PcClient] Pong send failed: %s", e)

    elif msg_type == "connect_relay_ack":
        # R1/R5: PC 收到 connect_relay 后回执，以 push_id 为 key resolve
        push_id = data.get("push_id")
        if push_id:
            fut = device._push_ack_pending.get(push_id)
            if fut and not fut.done():
                fut.set_result({"ok": True})

    elif msg_type == "ice_candidate":
        # Trickle ICE: PC → Gateway → App (AppBridge WS)
        session_id = data.get("session_id", "")
        candidate = data.get("candidate")
        device_id_for_ice = data.get("device_id", "")
        if candidate and device.user_id:
            from device.gateway_signaling import push_ice_candidate_to_user
            asyncio.ensure_future(
                push_ice_candidate_to_user(device.user_id, device_id_for_ice, session_id, candidate)
            )

    elif msg_type == "webrtc_answer":
        # WebRTC: PC → Gateway → App (SDP answer via WS)
        session_id = data.get("session_id", "")
        sdp_answer = data.get("sdp_answer", "")
        device_id_for_answer = data.get("device_id", "")
        if sdp_answer and device.user_id:
            from device.gateway_signaling import push_webrtc_answer_to_user
            asyncio.ensure_future(
                push_webrtc_answer_to_user(device.user_id, device_id_for_answer, session_id, sdp_answer)
            )

    elif msg_type == "vm_status_report":
        # VmControl 上报当前托管的 VM/AVD 列表（含 stopped），持久化到 devices.pc_client_id
        # 关系：user -> pc_client -> devices。pc_client_id 持久绑定，离线也保留。
        # 仅做写入，不清除。换用户登录时通过 pc_client online + device available 区分。
        # vm_ids=Linux device.id；android_serials=Android device.device_serial；android_avd_names=Android device.avd_name（含 stopped）
        vm_ids = set(data.get("vm_ids", []))
        android_serials = set(data.get("android_serials", []))
        android_avd_names = set(data.get("android_avd_names", []))
        device.vm_ids = vm_ids
        device.last_seen = datetime.utcnow()
        logger.info(
            "[PcClient] vm_status_report: %s hosts %d VM(s) + %d Android serial(s) + %d AVD(s)",
            device.device_id, len(vm_ids), len(android_serials), len(android_avd_names),
        )

        try:
            user_id = device.user_id or "local"  # 当前会话用户（x-user-id）
            # CR: user_id=local 时禁止 DB 更新，避免未认证连接导致跨用户 pc_client_id 绑定
            if user_id == "local":
                logger.debug("[PcClient] vm_status_report skipped (user_id=local, no DB update)")
            else:
                from device.entity_store import get_entity_store
                store = get_entity_store()
                pc_id = device.device_id

                # Linux VMs: 只更新已有设备的 pc_client_id + status，不自动创建
                from device.config_devices import DeviceStatus
                for vid in vm_ids:
                    if not vid:
                        continue
                    existing = store.get("devices", user_id, vid)
                    if existing:
                        store.update(
                            "devices", user_id, vid,
                            {"pc_client_id": pc_id, "status": DeviceStatus.READY.value},
                            notify=False,
                        )

                # Android by serial: 按非主键字段更新 → update_where
                for serial in android_serials:
                    if serial:
                        store.update_where(
                            "devices", user_id,
                            data={"pc_client_id": pc_id},
                            filters={"device_serial": serial, "type": "android"},
                        )

                # Android by AVD name: 按非主键字段更新 → update_where
                for avd_name in android_avd_names:
                    if avd_name:
                        store.update_where(
                            "devices", user_id,
                            data={"pc_client_id": pc_id},
                            filters={"avd_name": avd_name, "type": "android"},
                        )

                # Host Desktop（upsert：同一 pc_client 换用户登录时自动迁移归属）
                host_desktop_enabled = data.get("host_desktop_enabled", False)
                hd_device_id = f"hd-{pc_id}"
                if host_desktop_enabled:
                    from device.config_devices import DeviceStatus
                    hd_data = {
                        "id": hd_device_id,
                        "user_id": user_id,
                        "type": "host_desktop",
                        "name": f"Host Desktop ({device.machine_label or pc_id[:8]})",
                        "status": DeviceStatus.RUNNING.value,
                        "pc_client_id": pc_id,
                    }
                    store.upsert("devices", user_id, hd_device_id, hd_data, notify=False)
                else:
                    existing_hd = store.get("devices", user_id, hd_device_id)
                    if existing_hd:
                        store.update("devices", user_id, hd_device_id, {"status": "stopped"}, notify=False)
        except Exception as e:
            logger.warning("[PcClient] vm_status_report persist failed (non-fatal): %s", e)

        # ── 关键：DB 写完后立即回推 sync_devices ──────────────────────────────
        # vm_status_report 把 pc_client_id 绑定到 devices 后，
        # sync_devices 才能按 pc_client_id 过滤到正确的设备列表。
        # 这形成完整的反馈环：
        #   VmControl 上报 vm_ids → Gateway 绑定 pc_client_id → Gateway 推回 registry
        # 即使 connect 时的首次推送因时序问题空白，这里也会补救。
        user_id_for_sync = device.user_id or "local"
        asyncio.ensure_future(_push_sync_devices(device, user_id_for_sync))


# ─── WebSocket 端点 ────────────────────────────────────────────────────────────

@router.websocket("/pc/ws")
async def pc_client_websocket(websocket: WebSocket):
    """
    Tauri App 通过此 WebSocket 连接 Gateway。

    握手必须携带：
      x-device-id        pc_client_id（物理 PC 标识，VmControl 持久 UUID，必填）
      x-user-id          nginx 从 JWT 解析注入（Phase 4 前可选，缺失时 fallback "local"）
      x-app-instance-id  AppInstance 唯一 ID（可选，用于与 device_id 关联）
      x-machine-label    机器型号/主机名等标识（可选，便于展示）

    连接后 Gateway 将通过此连接转发来自 Tools Server 的 VmControl 请求。
    """
    device_id = websocket.headers.get("x-device-id", "").strip()
    user_id = websocket.headers.get("x-user-id", "").strip()
    app_instance_id = websocket.headers.get("x-app-instance-id", "").strip()
    machine_label = websocket.headers.get("x-machine-label", "").strip()

    if not device_id:
        # 兼容旧版 CloudBridge（未携带 device_id）：分配临时 ID，给出警告
        device_id = f"legacy-{str(uuid.uuid4())[:8]}"
        logger.warning(
            "[PcClient] Connection without x-device-id, assigned temp id=%s. "
            "Please upgrade to the latest NovAIC App.",
            device_id,
        )

    if not user_id:
        # Phase 1 过渡期：nginx 尚未配置 JWT 验证，fallback 到 "local"
        user_id = "local"
        logger.debug("[PcClient] No x-user-id for device %s, using 'local'", device_id)

    await websocket.accept()

    registry = get_device_registry()
    try:
        device = await registry.connect(
            websocket,
            device_id,
            user_id,
            app_instance_id=app_instance_id,
            machine_label=machine_label,
        )
    except ValueError as e:
        logger.warning("[PcClient] Rejected connection: %s", e)
        await websocket.close(4001, str(e))
        return

    try:
        from device.entity_store import get_entity_store
        store = get_entity_store()
        
        # update the pc_client status
        # Note: Since PcClient is not a synchronized entity yet, we bypass it for now.
        # But we could also add 'pc-client' to the EntityStore.
        # For now, if we don't have get_db(), we can skip the manual DB action and 
        # let ping handle online status
    except Exception as e:
        logger.warning("[PcClient] DB upsert failed (non-fatal): %s", e)

    # ── 连接后推送 Device Registry（全量）────────────────────────────────────
    # VmControl 收到后写入本地 SQLite，统一 WebRTC 入口靠此 registry 分发请求
    asyncio.ensure_future(_push_sync_devices(device, user_id))

    try:
        while True:
            data = await websocket.receive_json()
            await _handle_device_message(device, data)
    except WebSocketDisconnect:
        logger.info("[PcClient] Device %s disconnected normally", device_id)
    except Exception as e:
        logger.error("[PcClient] Device %s error: %s", device_id, e)
    finally:
        await registry.disconnect(websocket, device_id)


async def _push_sync_devices(device: DeviceState, user_id: str) -> None:
    """
    向 VmControl 推送该用户的设备列表（sync_devices 消息）。
    VmControl 收到后 upsert 到本地 SQLite Device Registry。
    触发时机：
      1. PC 连接建立后（全量推送）
      2. 设备状态变更时（增量推送），调用方直接 await 此函数
    """
    if user_id == "local":
        # 未认证连接，不推送
        logger.debug("[PcClient] sync_devices skipped (user_id=local)")
        return

    # 稍微等一下让 WS 完全建立
    await asyncio.sleep(0.2)

    try:
        from device.entity_store import get_entity_store
        store = get_entity_store()

        # 只推送绑定到该 PC 的设备（pc_client_id = device.device_id）
        # 同时包括该用户的 host_desktop（pc_client_id 以 hd- 开头）
        all_devices = store.list("devices", user_id)
        pc_id = device.device_id

        entries = []
        for d in all_devices:
            if d.get("pc_client_id") != pc_id:
                continue  # 不在本 PC 上的设备跳过

            # Extract fields safely from dict instead of ORM object
            d_id = d.get("id")
            ui = d.get("user_id")
            st = d.get("status")

            entry = {
                "device_id": d_id,
                "user_id": ui,
                # DeviceStatus mapping handling
                "status": st.value if hasattr(st, "value") else str(st) if st else "offline",
                "display_name": d.get("name"),
                "agent_id": None,
            }

            dev_type = d.get("type", "unknown")
            type_str = dev_type.value if hasattr(dev_type, "value") else str(dev_type)

            if type_str == "linux":
                entry["device_type"] = "linux_vm"
                entry["vm_id"] = d_id
            elif type_str == "host_desktop":
                entry["device_type"] = "host_desktop"
            elif type_str == "android":
                entry["device_type"] = "android"
                entry["device_serial"] = d.get("device_serial", None) or d_id
            else:
                entry["device_type"] = type_str
                entry["vm_id"] = d_id

            entries.append(entry)

        if not entries:
            logger.debug("[PcClient] sync_devices: no devices for pc=%s user=%s", pc_id, user_id)
            return

        msg = {"type": "sync_devices", "devices": entries}
        ws = device.ws
        if ws is not None:
            async with device._send_lock:
                await ws.send_json(msg)
            logger.info(
                "[PcClient] sync_devices pushed %d device(s) to pc=%s user=%s",
                len(entries), pc_id, user_id,
            )

    except Exception as e:
        logger.warning("[PcClient] sync_devices push failed (non-fatal): %s", e)
