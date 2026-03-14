# Phase 1 — 设备身份基础（Device Identity Foundation）

> 目标：为每台运行 VmControl 的 PC 建立唯一、持久、可验证的身份 ID，  
> 并将这个 ID 作为 CloudBridge 连接、P2P 打洞、Gateway 路由的统一索引键。  
> 本阶段完成后，Gateway 可正确区分同一用户的多台 PC。

---

## 一、背景与问题

### 当前状态

```
Gateway pc_client.py
  _manager = PcClientManager()   # 全局单例，一个用户只允许一个 PC 连接
  
  async def connect(ws):
      if self._ws is not None:
          await self._ws.close(1001, "New connection established")  # 踢掉旧连接！
          ...
```

**问题：**

| 问题 | 影响 |
|---|---|
| 全局单例 | 多用户互相覆盖 |
| per-user 后也是单连接 | 同一用户多台 PC 时互踢 |
| 无 `device_id` 概念 | 无法将 VM 路由到正确的 PC |
| CloudBridge 无身份标识 | WS 连接断后 Gateway 无法知道是哪台设备重连 |

### 目标状态

```
Gateway pc_client.py
  _devices: Dict[str, DeviceState] = {}   # device_id → 设备完整状态

  async def connect(ws, device_id, user_id):
      # 同一 device_id 重连时：继承旧 pending，迁移 WS
      # 新 device_id 首次连接：注册新条目
      # 不踢任何连接
```

---

## 二、核心概念：device_id

### 定义

`device_id` 是 **VmControl 在首次启动时生成的 Ed25519 公钥（hex 编码）**，持久化存储在本地，永久唯一标识这台 PC 上的 VmControl 实例。

```
device_id = hex(ed25519_public_key)   # 64 字节 → 128 字符 hex
                                       # 或使用 UUID（更简单，Phase 1 推荐）
```

> **Phase 1 简化方案**：使用随机 UUID v4，存入 `data_dir/device_id.txt`。  
> Ed25519 keypair 在 Phase 3（P2P 加密）时再引入，届时迁移 device_id 为公钥格式。

### 生命周期

```
VmControl 首次启动
  → 检查 data_dir/device_id.txt
  → 不存在：生成 UUID v4，写入文件
  → 存在：读取并使用
  → 持久不变（除非用户手动删除）
```

---

## 三、改动清单

```
Task 1  vmcontrol/src/config.rs        — 新增 device_id 字段，启动时加载/生成
Task 2  vmcontrol/src/cloud_bridge.rs  — WS 握手时发送 x-device-id header
Task 3  novaic-gateway/pc_client.py    — 重构为 per-device DeviceManager
Task 4  novaic-gateway/db/schema.py    — 新增 pc_clients 表（v48）
Task 5  novaic-gateway/api/vm.py       — 通过 device_id 路由请求
Task 6  main.rs（Tauri）               — 登录后触发 CloudBridge 立即重连
```

---

## 四、Task 1：VmControl device_id 生成

**文件：** `novaic-app/src-tauri/vmcontrol/src/config.rs`

### 当前代码

```rust
pub struct Config {
    pub runtime_dir: PathBuf,
}
```

### 改动后

```rust
use std::path::PathBuf;
use std::fs;

#[derive(Debug, Clone)]
pub struct Config {
    pub runtime_dir: PathBuf,
    pub data_dir: PathBuf,
    pub device_id: String,   // 新增：持久 UUID，跨重启不变
}

impl Config {
    /// 从 data_dir 加载配置，device_id 不存在时自动生成。
    pub fn load(data_dir: PathBuf) -> Self {
        let runtime_dir = data_dir.join("runtime");
        let device_id = load_or_generate_device_id(&data_dir);
        Self { runtime_dir, data_dir, device_id }
    }
}

fn load_or_generate_device_id(data_dir: &PathBuf) -> String {
    let id_file = data_dir.join("device_id.txt");
    if let Ok(id) = fs::read_to_string(&id_file) {
        let id = id.trim().to_string();
        if !id.is_empty() {
            tracing::info!("[VmControl] Loaded device_id: {}", id);
            return id;
        }
    }
    let new_id = uuid::Uuid::new_v4().to_string();
    let _ = fs::create_dir_all(data_dir);
    let _ = fs::write(&id_file, &new_id);
    tracing::info!("[VmControl] Generated new device_id: {}", new_id);
    new_id
}
```

---

## 五、Task 2：CloudBridge 发送 device_id header

**文件：** `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs`

### CloudBridgeConfig 新增字段

```rust
pub struct CloudBridgeConfig {
    pub gateway_url: Arc<std::sync::Mutex<String>>,
    pub cloud_token: Arc<tokio::sync::RwLock<String>>,
    pub device_id: String,   // 新增：来自 Config::device_id
}
```

### connect_and_run 握手时注入 header

```rust
// 改动位置：connect_and_run() 中构建 ws_request 的地方
let ws_request = match ws_url.into_client_request() {
    Ok(mut req) => {
        if !token.is_empty() {
            if let Ok(val) = format!("Bearer {}", token).parse() {
                req.headers_mut().insert(AUTHORIZATION, val);
            }
        }
        // ↓ 新增：携带 device_id
        if let Ok(val) = config.device_id.parse() {
            req.headers_mut().insert("x-device-id", val);
        }
        req
    }
    ...
};
```

### lib.rs：start_embedded_server 传入 device_id

```rust
// 在 start_embedded_server 调用处（main.rs），
// 从 Config::load() 获取 device_id，传给 CloudBridgeConfig
let vmcontrol_config = vmcontrol::Config::load(data_dir.clone());
let cloud_config = Some(vmcontrol::CloudBridgeConfig {
    gateway_url: Arc::clone(&gateway_url_state),
    cloud_token: Arc::clone(&cloud_token),
    device_id: vmcontrol_config.device_id.clone(),
});
vmcontrol::start_embedded_server(vmcontrol_config, cloud_config, shutdown_rx).await;
```

---

## 六、Task 3：Gateway pc_client.py 重构

**文件：** `novaic-gateway/gateway/api/internal/pc_client.py`

### 新数据结构

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set

@dataclass
class DeviceState:
    device_id: str
    user_id: str
    ws: Optional[WebSocket] = None
    online: bool = False                    # 是否开放 Agent 控制
    vm_ids: Set[str] = field(default_factory=set)
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    _pending: dict = field(default_factory=dict)
    _send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    @property
    def is_connected(self) -> bool:
        return self.ws is not None
```

### DeviceRegistry（替换 PcClientManager 单例）

```python
class DeviceRegistry:
    """管理所有已连接设备的 WebSocket 连接，以 device_id 为索引键。"""

    def __init__(self):
        self._devices: Dict[str, DeviceState] = {}
        self._registry_lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, device_id: str, user_id: str) -> DeviceState:
        """
        注册或更新设备连接。
        同一 device_id 重连时：迁移连接，继承 vm_ids 等状态，不踢 pending。
        不同 device_id 的设备并行共存。
        """
        async with self._registry_lock:
            if device_id in self._devices:
                device = self._devices[device_id]
                # 安全校验：device_id 不能被不同用户劫持
                if device.user_id != user_id:
                    logger.warning(
                        f"[DeviceRegistry] device_id {device_id} user_id mismatch: "
                        f"existing={device.user_id}, new={user_id}"
                    )
                    raise ValueError(f"device_id {device_id} belongs to different user")
                # 同 device_id 重连：关闭旧 WS，继承状态
                async with device._lock:
                    if device.ws is not None:
                        try:
                            await device.ws.close(1001, "Device reconnected")
                        except Exception:
                            pass
                    device.ws = ws
                    device.connected_at = datetime.utcnow()
                    device.last_seen = datetime.utcnow()
                logger.info(f"[DeviceRegistry] Device {device_id} reconnected (user={user_id})")
            else:
                # 首次连接：注册新设备
                device = DeviceState(
                    device_id=device_id,
                    user_id=user_id,
                    ws=ws,
                    connected_at=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                )
                self._devices[device_id] = device
                logger.info(f"[DeviceRegistry] New device {device_id} registered (user={user_id})")
            return device

    async def disconnect(self, ws: WebSocket, device_id: str) -> None:
        """
        断开连接。只置空 ws，保留 DeviceState（vm_ids 等状态保留）。
        下次同 device_id 重连时直接恢复。
        """
        async with self._registry_lock:
            device = self._devices.get(device_id)
            if device is None:
                return
            async with device._lock:
                if device.ws is not ws:
                    return  # 已经是新连接，不覆盖
                device.ws = None
                device.last_seen = datetime.utcnow()
                # 清理 pending futures，通知调用方连接已断
                for fut in device._pending.values():
                    if not fut.done():
                        fut.set_exception(ConnectionError("Device disconnected"))
                device._pending.clear()
        logger.info(f"[DeviceRegistry] Device {device_id} disconnected")

    def get_device(self, device_id: str) -> Optional[DeviceState]:
        return self._devices.get(device_id)

    def get_user_devices(self, user_id: str) -> List[DeviceState]:
        """返回指定用户的所有设备状态（含离线设备）。"""
        return [d for d in self._devices.values() if d.user_id == user_id]

    def get_connected_devices(self, user_id: str) -> List[DeviceState]:
        """返回指定用户当前在线的设备。"""
        return [d for d in self._devices.values() 
                if d.user_id == user_id and d.is_connected]


# 全局注册表（替换 _manager 单例）
_registry = DeviceRegistry()

def get_device_registry() -> DeviceRegistry:
    return _registry

# 兼容旧调用方：通过 user_id 获取第一台设备（过渡期用）
def get_pc_client_manager(user_id: Optional[str] = None):
    """
    过渡期兼容接口。
    新代码应直接使用 get_device_registry()。
    """
    if user_id is None:
        # 返回任意已连接设备（旧的全局单例行为）
        for device in _registry._devices.values():
            if device.is_connected:
                return _DeviceManagerAdapter(device)
        return _DisconnectedAdapter()
    # 返回该用户第一台已连接设备
    devices = _registry.get_connected_devices(user_id)
    if devices:
        return _DeviceManagerAdapter(devices[0])
    return _DisconnectedAdapter()
```

### WS 握手：读取 device_id header

```python
@router.websocket("/pc/ws")
async def pc_client_websocket(websocket: WebSocket):
    """
    Tauri App 连接此 WebSocket。
    握手时必须携带：
      - x-device-id header（VmControl 生成的持久 UUID）
      - Authorization: Bearer <jwt>（由 nginx 解析为 X-User-ID）
    """
    device_id = websocket.headers.get("x-device-id")
    user_id = websocket.headers.get("x-user-id")   # nginx 从 JWT 解析注入

    if not device_id:
        await websocket.close(4000, "Missing x-device-id header")
        return
    
    # Phase 1 过渡期：user_id 可能为空（本地模式，nginx 未启用 JWT）
    if not user_id:
        user_id = "local"
        logger.warning(f"[PcClient] No x-user-id for device {device_id}, using 'local'")

    await websocket.accept()
    
    registry = get_device_registry()
    try:
        device = await registry.connect(websocket, device_id, user_id)
    except ValueError as e:
        await websocket.close(4001, str(e))
        return

    try:
        while True:
            data = await websocket.receive_json()
            await _handle_device_message(device, data)
    except WebSocketDisconnect:
        logger.info(f"[PcClient] Device {device_id} disconnected normally")
    except Exception as e:
        logger.error(f"[PcClient] Device {device_id} error: {e}")
    finally:
        await registry.disconnect(websocket, device_id)


async def _handle_device_message(device: DeviceState, data: dict) -> None:
    """处理来自设备的消息（proxy_response / ping / vm_online_status）。"""
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
            except Exception:
                pass
    elif msg_type == "vm_status_report":
        # VmControl 上报托管的 VM 列表
        vm_ids = set(data.get("vm_ids", []))
        device.vm_ids = vm_ids
        device.last_seen = datetime.utcnow()
        logger.debug(f"[PcClient] Device {device.device_id} hosts VMs: {vm_ids}")
```

### DeviceState 的 forward_request 方法

```python
# 将 forward_request / send_control 从 PcClientManager 迁移到 DeviceState
# （保持接口完全一致，只是从 self._ws 改为 device.ws）

async def forward_to_device(
    device: DeviceState,
    method: str,
    path: str,
    body: bytes,
    headers: dict,
    timeout: float = 120.0,
) -> dict:
    """向指定设备转发 HTTP 请求并等待响应。"""
    ws = device.ws
    if ws is None:
        raise ConnectionError(f"Device {device.device_id} not connected")

    request_id = str(uuid.uuid4())
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
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
            raise ConnectionError(f"Failed to send to device {device.device_id}: {e}") from e

        return await asyncio.wait_for(fut, timeout=timeout)
    finally:
        device._pending.pop(request_id, None)
```

---

## 七、Task 4：Gateway DB Schema v48

**文件：** `novaic-gateway/gateway/db/schema.py`

### 新增 pc_clients 表（持久化设备注册信息）

> 注意：`devices` 表已存在，记录的是 VM/AVD 配置（agent 维度）。  
> 新增的 `pc_clients` 表记录的是 **运行 VmControl 的 PC 设备**（物理机维度），两者概念不同。

```sql
-- v48: pc_clients 表 — 记录每台运行 VmControl 的 PC 设备
-- 与 devices 表的区别：
--   devices: Agent 托管的 VM/AVD 配置（逻辑设备）
--   pc_clients: 物理 PC 机器注册表（VmControl 实例）
CREATE TABLE IF NOT EXISTS pc_clients (
    device_id   TEXT PRIMARY KEY,       -- VmControl 生成的持久 UUID
    user_id     TEXT NOT NULL,           -- 归属用户
    name        TEXT DEFAULT '',         -- 用户设置的友好名称（可选）
    online      INTEGER DEFAULT 0,       -- 是否开放 Agent 控制（0/1）
    first_seen  TEXT DEFAULT (datetime('now')),
    last_seen   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pc_clients_user ON pc_clients(user_id);
```

### Migration 函数

```python
# 在 run_migration_sync() 末尾添加 v48 分支：

if from_version < 48:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pc_clients (
            device_id   TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            name        TEXT DEFAULT '',
            online      INTEGER DEFAULT 0,
            first_seen  TEXT DEFAULT (datetime('now')),
            last_seen   TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pc_clients_user ON pc_clients(user_id)"
    )
    conn.execute("PRAGMA user_version = 48")
    print("[schema] Migration v48: Added pc_clients table")
```

### PcClientRepository

**文件：** `novaic-gateway/gateway/db/repositories/pc_client.py`（新建）

```python
"""
PC Client Repository — 物理 PC 设备注册表的 CRUD 操作。
"""
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from gateway.db.access import Database


@dataclass
class PcClientRecord:
    device_id: str
    user_id: str
    name: str = ''
    online: bool = False
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


class PcClientRepository:
    def __init__(self, db: Database):
        self.db = db

    def upsert(self, device_id: str, user_id: str) -> PcClientRecord:
        """首次连接时注册，重连时更新 last_seen。"""
        now = datetime.utcnow().isoformat()
        self.db.execute("""
            INSERT INTO pc_clients (device_id, user_id, first_seen, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET
                last_seen = excluded.last_seen
        """, (device_id, user_id, now, now))
        return self.get(device_id)

    def get(self, device_id: str) -> Optional[PcClientRecord]:
        row = self.db.fetchone(
            "SELECT * FROM pc_clients WHERE device_id = ?", (device_id,)
        )
        return PcClientRecord(**dict(zip(
            ['device_id', 'user_id', 'name', 'online', 'first_seen', 'last_seen'],
            row
        ))) if row else None

    def list_by_user(self, user_id: str) -> List[PcClientRecord]:
        rows = self.db.fetchall(
            "SELECT * FROM pc_clients WHERE user_id = ? ORDER BY last_seen DESC",
            (user_id,)
        )
        return [PcClientRecord(**dict(zip(
            ['device_id', 'user_id', 'name', 'online', 'first_seen', 'last_seen'], r
        ))) for r in rows]

    def set_online(self, device_id: str, online: bool) -> None:
        self.db.execute(
            "UPDATE pc_clients SET online = ? WHERE device_id = ?",
            (1 if online else 0, device_id)
        )

    def update_last_seen(self, device_id: str) -> None:
        now = datetime.utcnow().isoformat()
        self.db.execute(
            "UPDATE pc_clients SET last_seen = ? WHERE device_id = ?",
            (now, device_id)
        )
```

---

## 八、Task 5：vm.py 通过 device_id 路由

**文件：** `novaic-gateway/gateway/api/vm.py`

### 问题

目前 `vm.py` 调用 `get_pc_client_manager()` 获取全局单例，无法区分多台 PC。

Agent 控制 VM 的路由需要知道：**这个 VM 在哪台 PC 上？**

### 过渡期方案（Phase 1 简化）

Phase 1 不立即重构所有 vm.py 路由，使用适配层让旧代码无感知迁移：

```python
# pc_client.py 中添加适配器

class _DeviceManagerAdapter:
    """将 DeviceState 包装为 PcClientManager 兼容接口，过渡期使用。"""
    def __init__(self, device: DeviceState):
        self._device = device

    @property
    def is_connected(self) -> bool:
        return self._device.is_connected

    async def forward_request(self, method, path, body, headers, timeout=120.0):
        return await forward_to_device(self._device, method, path, body, headers, timeout)

    async def send_control(self, msg_type, payload, timeout=60.0):
        # 复用 forward_to_device 的逻辑，发送控制消息
        ws = self._device.ws
        if ws is None:
            raise ConnectionError(f"Device not connected")
        request_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._device._pending[request_id] = fut
        message = {"type": msg_type, "id": request_id, **payload}
        try:
            async with self._device._send_lock:
                await ws.send_json(message)
        except Exception as e:
            if not fut.done():
                fut.cancel()
            raise ConnectionError(str(e)) from e
        try:
            response = await asyncio.wait_for(fut, timeout=timeout)
            return {"status": response.get("status", 200), "body": response.get("body", {})}
        finally:
            self._device._pending.pop(request_id, None)

    # 所有快捷方法委托给 send_control（保持原有接口）
    async def vm_status(self, vm_id): ...
    async def vm_start(self, vm_id, body=None): ...
    # ... 同现有 PcClientManager 的所有方法


class _DisconnectedAdapter:
    """无设备连接时的空实现，返回 ConnectionError。"""
    is_connected = False

    async def forward_request(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")

    async def send_control(self, *args, **kwargs):
        raise ConnectionError("No PC client connected")
    # ...
```

### 长期方案（Phase 2 完成后执行）

在 `vm.py` 的各个路由中，从 `agent` 的 `pc_client_device_id` 字段（下面 Task 4b 新增）查找对应设备：

```python
# vm.py 示例（长期方案）
@router.post("/{agent_id}/start")
async def start_vm(agent_id: str, user=Depends(get_current_user)):
    agent = agent_repo.get(agent_id)
    device_id = agent.pc_client_device_id   # 新字段
    registry = get_device_registry()
    device = registry.get_device(device_id)
    if device is None or not device.is_connected:
        raise HTTPException(503, "PC client not connected")
    return await forward_to_device(device, "POST", f"/api/vms/{agent.vm_id}/start", ...)
```

---

## 九、Task 6：登录触发 CloudBridge 重连

**问题：** 目前 App 启动时 CloudBridge 立即尝试连接，但 JWT token 为空（用户未登录），导致反复连接失败。

**文件：** `novaic-app/src-tauri/src/main.rs` + `vmcontrol/src/cloud_bridge.rs`

### 方案：tokio::sync::Notify

```rust
// cloud_bridge.rs — 新增 login_notify 参数

pub struct CloudBridgeConfig {
    pub gateway_url: Arc<std::sync::Mutex<String>>,
    pub cloud_token: Arc<tokio::sync::RwLock<String>>,
    pub device_id: String,
    pub login_notify: Arc<tokio::sync::Notify>,  // 新增：登录信号
}

pub async fn start_cloud_bridge(
    config: CloudBridgeConfig,
    vmcontrol_base_url: String,
    shutdown: oneshot::Receiver<()>,
) {
    // ... notify/shutdown 设置不变 ...
    
    tracing::info!("[CloudBridge] Waiting for user login...");
    // 等待登录信号（第一次）
    tokio::select! {
        biased;
        _ = notify.notified() => return,  // 关闭信号优先
        _ = config.login_notify.notified() => {}
    }
    tracing::info!("[CloudBridge] Login detected, starting connection");
    
    loop {
        // ... 原有连接循环不变 ...
    }
}
```

```rust
// main.rs — 在 update_cloud_token 命令中发送登录信号

// 在 AppState 中添加 login_notify
struct AppState {
    // ...
    login_notify: Arc<tokio::sync::Notify>,
}

#[tauri::command]
async fn update_cloud_token(
    token: String,
    state: tauri::State<'_, CloudTokenState>,
    login_notify: tauri::State<'_, Arc<tokio::sync::Notify>>,
) -> Result<(), String> {
    let mut w = state.write().await;
    *w = token;
    login_notify.notify_one();  // 通知 CloudBridge 可以连接了
    Ok(())
}
```

---

## 十、接口汇总

### Gateway WS 端点改动

```
WebSocket /internal/pc/ws

新增必需 header：
  x-device-id: <device_uuid>     # VmControl 生成的持久 UUID
  Authorization: Bearer <jwt>    # 由 nginx 解析注入 X-User-ID（Phase 4 前可选）

握手逻辑：
  1. 读取 x-device-id（无则 close 4000）
  2. 读取 x-user-id（无则 fallback "local"）
  3. 调用 DeviceRegistry.connect(ws, device_id, user_id)
  4. 进入消息循环
  5. 断开时调用 DeviceRegistry.disconnect(ws, device_id)
```

### 新增 REST 接口（可选，用于 UI 展示已连接设备）

```
GET /api/pc-clients
  → 返回当前用户所有已注册 PC 设备（含离线）
  → [{ device_id, name, online, is_connected, last_seen }]

GET /api/pc-clients/{device_id}/health
  → 透传到该设备的 /health 端点
  → 用于前端显示 VmControl 是否健康
```

---

## 十一、兼容性与迁移策略

| 兼容项 | 处理方式 |
|---|---|
| 旧版 CloudBridge（无 x-device-id header） | Gateway 为空 device_id 分配随机 UUID，日志警告 |
| 旧版 `get_pc_client_manager()` 调用方 | `_DeviceManagerAdapter` 包装，接口完全兼容 |
| `devices` 表（VM 配置）vs `pc_clients` 表（PC 机器） | 概念分离，不冲突 |
| 本地模式（无 nginx，无 JWT） | user_id fallback 为 "local"，功能正常 |

---

## 十二、验证方案

### 验证步骤

```bash
# 1. 启动 NovAIC App
# 2. 检查 VmControl 是否生成 device_id
cat ~/Library/Application\ Support/novaic/device_id.txt
# 输出：6e8a1f2c-3d4b-5e6f-7a8b-9c0d1e2f3a4b

# 3. 检查 Gateway 日志
# 应看到：[DeviceRegistry] New device 6e8a1f2c... registered (user=local)

# 4. 关闭重启 App
# 应看到：[DeviceRegistry] Device 6e8a1f2c... reconnected (user=local)
# 而非重新生成新的 device_id

# 5. 模拟两个设备连接（两个 VmControl 实例）
# 两条记录应独立共存，互不影响
```

### 检查清单

- [ ] `device_id.txt` 跨重启不变
- [ ] CloudBridge 握手 WS 请求头含 `x-device-id`
- [ ] Gateway 日志正确区分设备
- [ ] `pc_clients` 表有正确记录
- [ ] 两台 PC 同时连接时，`_devices` 有两条独立记录
- [ ] 旧的 `vm.py` 路由通过适配器正常工作

---

## 十三、完成标准

Phase 1 完成的判断标准：

1. ✅ 每台 PC 有持久 `device_id`，重启不变
2. ✅ Gateway 能区分多台 PC 的 CloudBridge 连接
3. ✅ 旧有的 VM 控制路由通过适配器继续工作
4. ✅ `pc_clients` 表记录了设备注册信息
5. ✅ 登录后 CloudBridge 立即建立连接（不再空 token 重试）
6. ⬜ P2P 相关字段（ext_ip/ext_port）留空，Phase 3 填充
