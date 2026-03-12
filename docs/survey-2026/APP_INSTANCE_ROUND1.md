# NovAIC App Instance 管理调研（Round 1）

**输入**：`novaic-app/src-tauri/src/state/mod.rs`（AppInstance）、`novaic-app/src/stores/`、`novaic-gateway` DeviceRegistry、`api.p2p` my-devices

**产出日期**：2026-03-12

---

## 1. 定义与生命周期（进程级 UUID）

### 1.1 定义

**AppInstance** 是 NovAIC 的统一身份抽象，桌面端（host）与移动端（viewer）共用同一结构：

```rust
// novaic-app/src-tauri/src/state/mod.rs
pub struct AppInstance {
    pub app_instance_id: String,   // 本实例唯一 ID（UUID v4）
    pub app_type: AppType,          // Desktop | Mobile
    pub machine_label: String,       // 机器型号/主机名等标识
    pub is_ready: bool,             // 登录后为 true
}
```

- **app_instance_id**：进程级 UUID，每次 Tauri 进程启动时生成，**不持久化**
- **app_type**：`Desktop`（有 VmControl/P2P）或 `Mobile`（纯 viewer）
- **machine_label**：来自 `crate::platform::device_info::machine_label()`，便于 Gateway 展示
- **is_ready**：登录后置为 `true`，表示可进行 VNC/relay 等操作

### 1.2 生命周期

| 阶段 | 行为 |
|------|------|
| **进程启动** | `AppInstance::new_desktop()` / `new_mobile()` 生成新 UUID |
| **登录前** | `is_ready = false` |
| **登录** | `update_cloud_token` → `login_notify.notify_one()` → `spawn_app_instance_ready_task` 置 `is_ready = true` |
| **进程退出** | 状态销毁，下次启动重新生成 |

**关键点**：`app_instance_id` 与进程绑定，重启即变；与持久化的 `device_id`（VmControl Ed25519）不同。

---

## 2. 生成与存储

### 2.1 setup.rs 生成

```rust
// novaic-app/src-tauri/src/setup.rs
let app_instance: AppInstanceState = Arc::new(tokio::sync::RwLock::new(
    if cfg!(not(any(target_os = "android", target_os = "ios"))) {
        AppInstance::new_desktop()
    } else {
        AppInstance::new_mobile()
    },
));
app.manage(app_instance.clone());
```

- 在 `setup_shared()` 中创建，早于 VmControl 启动
- 使用 `Arc<RwLock<AppInstance>>` 共享，通过 `tauri::State` 注入

### 2.2 AppInstanceState 存储

- **类型**：`Arc<RwLock<AppInstance>>`
- **位置**：Tauri 进程内，`app.manage()` 注入
- **可写时机**：`set_ready()` 在登录后由 `spawn_app_instance_ready_task` 调用

### 2.3 前端 Store 同步

```typescript
// novaic-app/src/application/store.ts
appInstanceId: string | null;  // P2-5: 供 my-devices 等调用时标注 is_local
```

```typescript
// novaic-app/src/App.tsx
useEffect(() => {
  invoke<{ app_instance_id: string }>('get_app_instance')
    .then((inst) => {
      if (inst?.app_instance_id)
        useAppStore.getState().patchState({ appInstanceId: inst.app_instance_id });
    })
    .catch(() => {});
}, []);
```

- 前端通过 `get_app_instance` 命令获取，写入 `useAppStore.appInstanceId`
- 尽早获取（App 挂载时），供 my-devices、resolveCurrentPcClientId 等使用

### 2.4 Gateway 存储（DeviceRegistry）

```python
# novaic-gateway/gateway/api/internal/pc_client.py
@dataclass
class DeviceState:
    device_id: str
    user_id: str
    app_instance_id: str = ""   # 来自 x-app-instance-id header
    machine_label: str = ""    # 来自 x-machine-label header
    # ...
```

- **来源**：Cloud Bridge WebSocket 握手时 `x-app-instance-id` header
- **关联**：以 `device_id` 为键，`app_instance_id` 作为 DeviceState 字段存储
- **用途**：`get_device_by_app_instance_id()` 反向查找 device_id

---

## 3. 使用场景

### 3.1 my-devices 与 is_local

**API**：`GET /api/p2p/my-devices?current_app_instance_id={id}`

**流程**：

1. 前端/命令传入 `current_app_instance_id`（本机 app_instance_id）
2. Gateway 调用 `registry.get_device_by_app_instance_id(current_app_instance_id)` 得到 DeviceState
3. 取 `dev.device_id` 作为 `current_pc_client_id`
4. `_build_device_item()` 中，当 `entry.device_id == current_pc_client_id` 时设置 `item["is_local"] = True`
5. 按 `app_instance_id` 分组到 `by_app_instance`，本机所在楼层标 `is_local: true`

**调用处**：

| 调用方 | 文件 | 说明 |
|--------|------|------|
| `get_vnc_proxy_url` | `vnc_urls.rs` | 移动端无 local_vmcontrol 时，传 app_id 取 my-devices |
| `get_scrcpy_proxy_url` | `vnc_urls.rs` | 同上 |
| `vnc_bridge_connect` → `resolve_device_id` | `vnc_bridge.rs` | 同上 |
| `api.p2p.getMyDevices` | `api.ts` | 前端传 `currentAppInstanceId` 获取带 is_local 的设备列表 |

### 3.2 Cloud Bridge x-app-instance-id

**流程**：

1. `lib.rs` 启动 VmControl 时，从 `AppInstanceState` 读取 `app_instance_id`、`machine_label`
2. 传入 `CloudBridgeConfig { app_instance_id, machine_label, ... }`
3. `connect_and_run()` 建立 WebSocket 时设置 header：
   - `x-device-id`：VmControl 持久 device_id
   - `x-app-instance-id`：AppInstance UUID
   - `x-machine-label`：机器标识

```rust
// novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs
if !app_instance_id.is_empty() {
    req.headers_mut().insert("x-app-instance-id", val);
}
```

4. Gateway `pc_client_websocket` 从 header 解析，写入 `DeviceRegistry.connect(..., app_instance_id=app_instance_id)`

### 3.3 resolveCurrentPcClientId

**用途**：多 PC 场景下，解析「当前 PC」的 `pc_client_id`，用于 AddAndroidModal、AddLinuxVMUserModal 等创建设备时指定目标 PC。

**实现**：

```typescript
// novaic-app/src/services/api.ts
resolveCurrentPcClientId: async (appInstanceId: string | null): Promise<string | undefined> => {
  if (!appInstanceId) return undefined;
  const res = await api.p2p.getMyDevices(appInstanceId);
  const local = res.devices?.find((d) => d.is_local);
  return local?.device_id ?? local?.pc_client_id ?? res.devices?.[0]?.device_id;
}
```

**逻辑**：传 `appInstanceId` → 调 `getMyDevices(appInstanceId)` → 取 `is_local` 设备 → 否则退化为 `devices[0]`

**调用处**：

- `AddAndroidModal.tsx`：创建 Android 设备时 `resolveCurrentPcClientId(appInstanceId)`
- `AddLinuxVMUserModal.tsx`：创建 Linux 子用户设备时同上

**注意**：若 `appInstanceId` 未同步（如登录后立即操作），`resolveCurrentPcClientId(null)` 直接返回 `undefined`，Modal 会报错「请选择目标 PC 或确保 Tauri 应用已连接」。

---

## 4. 与 device_id、pc_client_id 的关系

### 4.1 概念区分

| 标识 | 含义 | 生成/来源 | 持久化 | 作用域 |
|------|------|-----------|--------|--------|
| **app_instance_id** | 应用实例（进程）唯一 ID | Tauri 启动时 `uuid::Uuid::new_v4()` | 否 | 单进程 |
| **device_id** | 物理 PC 标识（VmControl） | VmControl `load_or_generate_device_id`（Ed25519 派生） | 是（data_dir） | 单机 |
| **pc_client_id** | 与 device_id 同值 | 兼容别名 | 同上 | 同上 |

### 4.2 关联关系

```
┌─────────────────────────────────────────────────────────────────┐
│  Tauri 进程（桌面端）                                              │
│  ┌──────────────────┐     ┌─────────────────────────────────┐  │
│  │ AppInstance       │     │ VmControl                        │  │
│  │ app_instance_id   │     │ device_id (持久)                  │  │
│  │ (进程级 UUID)     │     │ (pc_client_id 同值)               │  │
│  └────────┬─────────┘     └──────────────┬────────────────────┘  │
│           │                              │                       │
│           │    Cloud Bridge WS 握手       │                       │
│           │    x-app-instance-id         │  x-device-id          │
└───────────┼──────────────────────────────┼───────────────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────────────────────────────────────────────────┐
│  Gateway DeviceRegistry                                            │
│  DeviceState { device_id, app_instance_id, machine_label, ... }    │
│  以 device_id 为键；app_instance_id 用于 get_device_by_app_instance_id │
└───────────────────────────────────────────────────────────────────┘
```

### 4.3 多 PC 场景

- 同一用户多台 PC：每台有独立 `device_id`、`app_instance_id`
- `device_id` 由 VmControl 持久化，同一台 PC 重启不变
- `app_instance_id` 每次 Tauri 重启都变，但 Cloud Bridge 重连时会更新 DeviceRegistry 中的 `app_instance_id`
- `my-devices` 通过 `current_app_instance_id` 查 `get_device_by_app_instance_id` 得到当前请求方对应的 `device_id`，从而标注 `is_local`

### 4.4 数据流小结

| 方向 | 路径 |
|------|------|
| App → Gateway | Cloud Bridge WS：`x-app-instance-id` + `x-device-id` → DeviceRegistry 关联 |
| Gateway → 前端 | my-devices：`current_app_instance_id` → 查 DeviceRegistry → 标 is_local |
| 前端 → 多 PC 路由 | `resolveCurrentPcClientId(appInstanceId)` → getMyDevices → is_local 设备 → pc_client_id |

---

## 附录：代码索引

| 模块 | 路径 |
|------|------|
| AppInstance 定义 | `novaic-app/src-tauri/src/state/mod.rs` |
| setup 注入 | `novaic-app/src-tauri/src/setup.rs` |
| get_app_instance 命令 | `novaic-app/src-tauri/src/commands/app_instance.rs` |
| 前端 store | `novaic-app/src/application/store.ts` |
| App 同步 | `novaic-app/src/App.tsx` |
| Cloud Bridge 配置 | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` |
| lib.rs 传入 CloudBridge | `novaic-app/src-tauri/src/lib.rs` |
| DeviceRegistry | `novaic-gateway/gateway/api/internal/pc_client.py` |
| my-devices API | `novaic-gateway/gateway/api/p2p.py` |
| getMyDevices / resolveCurrentPcClientId | `novaic-app/src/services/api.ts` |
| vnc_urls / vnc_bridge | `novaic-app/src-tauri/src/commands/vnc_urls.rs`, `vnc_bridge.rs` |
