# 第二轮调研（中层）：app_instance 与 my-devices 联动

## 1. my-devices 如何用 current_app_instance_id 标注 is_local

### 1.1 API 入口

| 项目 | 说明 |
|------|------|
| **端点** | `GET /api/p2p/my-devices` |
| **查询参数** | `current_app_instance_id`（推荐）、`current_device_id`（兼容旧版，若同时提供则忽略） |
| **位置** | `novaic-gateway/gateway/api/p2p.py:329-378` |

### 1.2 标注流程

```
1. 接收 current_app_instance_id（或 current_device_id）
2. 若 current_app_instance_id 非空：
   → registry.get_device_by_app_instance_id(current_app_instance_id)
   → 若找到 dev：current_pc_client_id = dev.device_id
3. 若 current_device_id 非空（且 current_app_instance_id 为空）：
   → current_pc_client_id = current_device_id
4. 遍历 _p2p_registry 中该 user 的所有 entry：
   → 调用 _build_device_item(entry, registry, current_pc_client_id)
   → 若 entry.device_id == current_pc_client_id：item["is_local"] = True
5. 按 app_instance_id 分组到 by_app_instance：
   → 若某 device 有 is_local，则该 app_instance 组 is_local = True
```

### 1.3 关键代码

```python
# p2p.py:344-372
if current_app_instance_id.strip():
    dev = registry.get_device_by_app_instance_id(current_app_instance_id.strip())
    if dev:
        current_pc_client_id = dev.device_id
# ...
result.append(_build_device_item(entry, registry, current_pc_client_id=current_pc_client_id))

# _build_device_item (p2p.py:318-319)
if current_pc_client_id and entry.device_id == current_pc_client_id:
    item["is_local"] = True

# by_app_instance 分组 (p2p.py:370-371)
if item.get("is_local"):
    by_app_instance[app_id]["is_local"] = True
```

### 1.4 数据来源

| 数据 | 来源 |
|------|------|
| **devices 列表** | `_p2p_registry`（P2P 心跳注册） |
| **app_instance_id、machine_label** | `DeviceRegistry`（Cloud Bridge WebSocket 连接时上报） |
| **current_pc_client_id** | `current_app_instance_id` → `get_device_by_app_instance_id` → `dev.device_id` |

---

## 2. DeviceRegistry 中 app_instance 与 device 的映射

### 2.1 数据结构

| 注册表 | 主键 | 含 app_instance_id? | 说明 |
|--------|------|----------------------|------|
| **DeviceRegistry** | device_id | ✅ DeviceState.app_instance_id | Cloud Bridge WebSocket 连接时存储 |
| **_p2p_registry** | device_id | ❌ P2PEntry 无此字段 | P2P 心跳只上报 device_id, ext_addr, cert 等 |

### 2.2 DeviceState 字段

```python
# pc_client.py:31-46
@dataclass
class DeviceState:
    device_id: str
    user_id: str
    ws: Optional[WebSocket] = None
    app_instance_id: str = ""   # x-app-instance-id
    machine_label: str = ""     # x-machine-label
    # ...
```

### 2.3 映射关系

| 方向 | 方法 | 逻辑 |
|------|------|------|
| **device_id → DeviceState** | `get_device(device_id)` | 直接字典查找 |
| **app_instance_id → DeviceState** | `get_device_by_app_instance_id(app_instance_id)` | 遍历 `_devices`，匹配 `d.app_instance_id == aid and d.is_connected` |

```python
# pc_client.py:153-161
def get_device_by_app_instance_id(self, app_instance_id: str) -> Optional[DeviceState]:
    if not app_instance_id or not app_instance_id.strip():
        return None
    aid = app_instance_id.strip()
    for d in self._devices.values():
        if d.app_instance_id == aid and d.is_connected:
            return d
    return None
```

### 2.4 映射建立时机

| 步骤 | 位置 | 说明 |
|------|------|------|
| 1 | Tauri Cloud Bridge 连接 | `cloud_bridge.rs:189-192` 在 WebSocket 请求中设置 `x-app-instance-id` header |
| 2 | Gateway WebSocket 接受 | `pc_client.py:580` 读取 `x-app-instance-id` |
| 3 | registry.connect | `pc_client.py:600-606` 将 `app_instance_id` 传入，写入 `DeviceState` |

**约束**：`get_device_by_app_instance_id` 要求 `d.is_connected`，即 Cloud Bridge 必须已连接且未断开，否则反查失败，`is_local` 不会被标注。

---

## 3. 前端/Tauri 获取 app_instance_id 的时机

### 3.1 Tauri 侧

| 时机 | 位置 | 说明 |
|------|------|------|
| **生成** | `setup.rs:54-60` | `AppInstance::new_desktop()` / `new_mobile()`，Tauri 启动即创建 |
| **存储** | `state/mod.rs:58,67` | `uuid::Uuid::new_v4().to_string()` |
| **可用** | 任意时刻 | `app.manage(app_instance)` 注入后，`get_app_instance` 命令即可返回 |

### 3.2 前端侧

| 时机 | 位置 | 说明 |
|------|------|------|
| **获取** | `App.tsx:203-206` | `useEffect` 依赖 `isSignedIn`，登录后调用 `invoke('get_app_instance')` |
| **存储** | `useAppStore.appInstanceId` | `patchState({ appInstanceId: inst.app_instance_id })` |
| **使用** | `AddAndroidModal`、`AddLinuxVMUserModal`、`api.p2p.getMyDevices` | 通过 `useAppStore((s) => s.appInstanceId)` 或参数传入 |

### 3.3 时序关系

```
Tauri 启动
  → AppInstance 创建（app_instance_id 立即可用）
  → setup_shared 完成
  → lib.rs spawn: VmControl.start(CloudBridgeConfig{ app_instance_id, ... })
  → Cloud Bridge 等待 cloud_token（登录后才有）
  → 用户登录 → cloud_token 推送 → Cloud Bridge 连接 Gateway
  → Gateway DeviceRegistry 建立 app_instance_id ↔ device_id 映射

前端
  → isSignedIn 后 useEffect 执行
  → invoke('get_app_instance') → useAppStore.appInstanceId
  → 后续 getMyDevices(appInstanceId)、resolveCurrentPcClientId(appInstanceId) 可用
```

**注意**：`app_instance_id` 在 Tauri 启动时就有，但前端只在 `isSignedIn` 后写入 store；Rust 命令（`get_vnc_proxy_url`、`vnc_bridge_connect` 等）直接从 `AppInstanceState` 读取，不依赖前端。

### 3.4 调用方与传参

| 调用方 | 传 current_app_instance_id? | 来源 |
|--------|-----------------------------|------|
| `get_vnc_proxy_url` | ✅ | `app_instance.read().await.app_instance_id` |
| `get_scrcpy_proxy_url` | ✅ | 同上 |
| `vnc_bridge_connect` | ✅ | 同上 |
| `api.p2p.getMyDevices(currentAppInstanceId)` | 可选 | `useAppStore.appInstanceId`，调用方需传入 |
| `api.p2p.resolveCurrentPcClientId(appInstanceId)` | 间接 | 内部调用 getMyDevices(appInstanceId) |

---

## 4. app_instance → is_local 决策链

### 4.1 完整决策链

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. 本机 Tauri 启动                                                                │
│    AppInstance::new_desktop() → app_instance_id = uuid::Uuid::new_v4()           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 2. Cloud Bridge 连接 Gateway（用户登录后）                                         │
│    WebSocket header: x-device-id, x-app-instance-id, x-machine-label            │
│    Gateway: registry.connect(..., app_instance_id=...)                          │
│    DeviceRegistry: device_id ↔ app_instance_id 映射建立                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 3. 调用方请求 my-devices                                                          │
│    • Rust: get_vnc_proxy_url / vnc_bridge_connect 等                              │
│      → 从 AppInstanceState 读 app_instance_id                                     │
│      → GET /api/p2p/my-devices?current_app_instance_id={id}                       │
│    • 前端: api.p2p.getMyDevices(appInstanceId)                                    │
│      → 同上（需调用方传入 appInstanceId）                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 4. Gateway 处理                                                                   │
│    current_app_instance_id 非空                                                    │
│      → registry.get_device_by_app_instance_id(current_app_instance_id)           │
│      → 若找到且 is_connected: current_pc_client_id = dev.device_id                │
│      → 若未找到: current_pc_client_id = ""，无设备被标 is_local                    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 5. 构建 devices 列表                                                              │
│    遍历 _p2p_registry（P2P 心跳注册的设备）                                        │
│    → _build_device_item(entry, registry, current_pc_client_id)                    │
│    → 若 entry.device_id == current_pc_client_id: item["is_local"] = True          │
│    → 从 registry 补充 item["app_instance_id"], item["machine_label"]              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 6. 按 app_instance 分组                                                           │
│    by_app_instance[app_id]["devices"].append(item)                               │
│    若 item.get("is_local"): by_app_instance[app_id]["is_local"] = True            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 7. 返回                                                                           │
│    { devices: [...], by_app_instance: [...] }                                      │
│    • devices[i].is_local 表示该设备是否为本机                                      │
│    • by_app_instance[j].is_local 表示该楼层是否含本机设备                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 失败条件

| 条件 | 结果 |
|------|------|
| 未传 `current_app_instance_id` | `current_pc_client_id = ""`，所有设备 `is_local` 均为未设置 |
| Cloud Bridge 未连接 | DeviceRegistry 无该 app_instance_id，`get_device_by_app_instance_id` 返回 None |
| Cloud Bridge 已断开 | `d.is_connected` 为 False，反查排除该设备 |
| app_instance_id 与 device_id 未同时出现在两表 | `_p2p_registry` 有 device（P2P 心跳）但 DeviceRegistry 无 app_instance_id，或反之，导致无法匹配 |

### 4.3 两表协同

```
_p2p_registry (P2P 心跳)          DeviceRegistry (Cloud Bridge)
device_id, user_id, ext_addr      device_id, app_instance_id, machine_label
        │                                    │
        └────────── 合并 by device_id ────────┘
                    │
                    ▼
            my-devices 返回的每个 device 项
            = P2PEntry 数据 + DeviceState.app_instance_id/machine_label
```

`is_local` 标注依赖：**调用方传入的 current_app_instance_id** 能在 DeviceRegistry 中反查到 device_id，且该 device_id 存在于 _p2p_registry 中。

---

## 5. 小结

| 主题 | 结论 |
|------|------|
| **my-devices 标注 is_local** | 通过 `current_app_instance_id` → `get_device_by_app_instance_id` → `current_pc_client_id` → `entry.device_id == current_pc_client_id` |
| **DeviceRegistry 映射** | `device_id` 为主键；`app_instance_id` 存于 DeviceState；`get_device_by_app_instance_id` 遍历反查，且要求 `is_connected` |
| **app_instance_id 获取时机** | Tauri 启动即生成；前端在 isSignedIn 后写入 store；Rust 命令直接从 AppInstanceState 读取 |
| **决策链** | app_instance_id → DeviceRegistry 反查 → device_id → 与 _p2p_registry 条目匹配 → is_local |
