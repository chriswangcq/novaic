# App Instance 管理概览（第一轮调研）

## 1. app_instance_id 定义

### 1.1 含义

| 属性 | 说明 |
|------|------|
| **类型** | UUID v4 字符串 |
| **语义** | 一次应用运行实例的唯一标识，生命周期等于进程生命周期 |
| **与 pc_client_id 关系** | 多对一：同一台物理机可多次启动应用，每次生成新的 app_instance_id |
| **与 device_id 关系** | app_instance_id 每次启动新建；device_id 持久化（VmControl Ed25519） |
| **职责边界** | 仅用于标识「这次运行」和关联「哪台物理机」，不参与业务逻辑 |

### 1.2 生成时机

| 时机 | 位置 | 代码 |
|------|------|------|
| **Tauri 启动** | `setup.rs:54-60` | `AppInstance::new_desktop()` / `AppInstance::new_mobile()` |
| **生成方式** | `state/mod.rs:58,67` | `uuid::Uuid::new_v4().to_string()` |

### 1.3 存储位置

| 层级 | 位置 | 说明 |
|------|------|------|
| **Rust 内存** | `AppInstanceState` (Arc<RwLock<AppInstance>>) | setup 时创建，`app.manage()` 注入 |
| **前端 Store** | `useAppStore.appInstanceId` | App.tsx 启动时 `get_app_instance` 写入 |
| **Gateway 内存** | `DeviceRegistry.DeviceState.app_instance_id` | Cloud Bridge WebSocket 连接时从 header 读取并存储 |

---

## 2. app_instance 使用场景

### 2.1 my-devices API（is_local 标注）

| 场景 | 说明 |
|------|------|
| **调用方** | `get_vnc_proxy_url`、`get_scrcpy_proxy_url`、`vnc_bridge_connect`、`api.p2p.getMyDevices` |
| **参数** | `current_app_instance_id={app_id}` |
| **Gateway 逻辑** | `registry.get_device_by_app_instance_id()` 查到对应 pc_client_id，在 devices 和 by_app_instance 中标记 `is_local` |
| **用途** | 前端区分「本机设备」与「远端设备」，用于 UI 展示和 VNC 路由选择 |

### 2.2 is_local 判断

| 场景 | 说明 |
|------|------|
| **VNC proxy URL 选择** | 移动端无 local_vmcontrol 时，调用 my-devices 取第一个 online 设备；传入 current_app_instance_id 使本机楼层标 is_local |
| **Bridge vs Local** | 根据 `is_local` 决定走本地直连还是 bridge/relay |
| **多 PC 路由** | `resolveCurrentPcClientId(appInstanceId)` 通过 my-devices 解析当前 PC 的 pc_client_id |

### 2.3 VNC 路由

| 场景 | 说明 |
|------|------|
| **VNC 路由本身** | 使用 `pc_client_id` / `device_id`，**不直接使用** app_instance_id |
| **间接使用** | 移动端解析目标 device_id 时，通过 my-devices（带 current_app_instance_id）获取设备列表 |

### 2.4 Cloud Bridge → Gateway 关联

| 场景 | 说明 |
|------|------|
| **WebSocket 握手** | Cloud Bridge 连接 `/internal/pc/ws` 时携带 `x-app-instance-id` header |
| **DeviceRegistry** | Gateway 将 app_instance_id 与 device_id 关联存储 |
| **my-devices 反查** | 前端传 current_app_instance_id 时，Gateway 用 `get_device_by_app_instance_id` 反查 pc_client_id |

---

## 3. 相关 API 与 Store

### 3.1 Tauri Commands

| Command | 文件 | 说明 |
|---------|------|------|
| `get_app_instance` | `commands/app_instance.rs` | 返回 `{ app_instance_id, app_type, machine_label, is_ready }` |
| `get_local_device_id` | `commands/app_instance.rs` | 返回本机 device_id（桌面端 P2P 启动后有值，移动端 None） |

### 3.2 前端 API

| API | 文件 | 说明 |
|-----|------|------|
| `api.p2p.getMyDevices(currentAppInstanceId?)` | `services/api.ts:1016-1024` | 调用 `gateway_get`，可选传 `current_app_instance_id` |
| `api.p2p.resolveCurrentPcClientId(appInstanceId)` | `services/api.ts:1026-1035` | 通过 getMyDevices 解析当前 PC 的 pc_client_id |

### 3.3 Gateway API

| API | 文件 | 说明 |
|-----|------|------|
| `GET /api/p2p/my-devices` | `gateway/api/p2p.py:328-378` | 查询参数：`current_app_instance_id`（推荐）、`current_device_id`（兼容） |
| `registry.get_device_by_app_instance_id()` | `gateway/api/internal/pc_client.py:153-164` | 根据 app_instance_id 查找 DeviceState |

### 3.4 Store

| Store | 字段 | 文件 | 说明 |
|-------|------|------|------|
| `useAppStore` | `appInstanceId: string \| null` | `application/store.ts:100-101, 173` | P2-5：供 my-devices 等调用时标注 is_local |

---

## 4. App Instance 生命周期

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 创建（Tauri 启动）                                                         │
│    setup.rs:54-60 → AppInstance::new_desktop() / new_mobile()                │
│    app_instance_id = uuid::Uuid::new_v4().to_string()                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 注入与同步                                                                │
│    • app.manage(app_instance) → Tauri State                                 │
│    • lib.rs:249-278 → CloudBridgeConfig 携带 app_instance_id, machine_label  │
│    • Cloud Bridge WebSocket → x-app-instance-id header → Gateway DeviceRegistry │
│    • App.tsx:203-206 → get_app_instance → useAppStore.patchState({ appInstanceId }) │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Ready（登录后）                                                            │
│    • update_cloud_token → login_notify.notify_one() + app_instance.set_ready() │
│    • spawn_app_instance_ready_task 监听 login_notify → set_ready()           │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. 使用期                                                                    │
│    • get_vnc_proxy_url / get_scrcpy_proxy_url / vnc_bridge_connect           │
│      → 从 AppInstanceState 读 app_instance_id → my-devices?current_app_instance_id= │
│    • api.p2p.getMyDevices(appInstanceId) / resolveCurrentPcClientId          │
│    • AddAndroidModal / AddLinuxVMUserModal → resolveCurrentPcClientId        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. 销毁（进程退出）                                                           │
│    • AppInstanceState 随进程结束释放                                          │
│    • Gateway DeviceRegistry 中该 device_id 的 app_instance_id 在重连时更新   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 使用点清单

| # | 使用点 | 文件 | 用途 |
|---|--------|------|------|
| 1 | AppInstance 创建 | `state/mod.rs`, `setup.rs` | 生成 app_instance_id |
| 2 | CloudBridgeConfig | `lib.rs:273-278` | 传给 Cloud Bridge 连接 Gateway |
| 3 | Cloud Bridge WebSocket | `vmcontrol/cloud_bridge.rs:189-192` | x-app-instance-id header |
| 4 | Gateway WebSocket 接受 | `pc_client.py:580,605` | 读取 header，registry.connect |
| 5 | DeviceRegistry | `pc_client.py:41,74,105-106,153-164` | 存储、反查 app_instance_id |
| 6 | my-devices API | `p2p.py:332-346,357-372` | current_app_instance_id 参数，is_local 标注，by_app_instance 分组 |
| 7 | get_vnc_proxy_url | `commands/vnc_urls.rs:39-46` | 构造 my-devices 请求 |
| 8 | get_scrcpy_proxy_url | `commands/vnc_urls.rs:96-103` | 同上 |
| 9 | vnc_bridge_connect | `commands/vnc_bridge.rs:50-57` | resolve_device_id 中构造 my-devices 请求 |
| 10 | get_app_instance | `commands/app_instance.rs` | 供前端读取 |
| 11 | App.tsx 启动 | `App.tsx:203-206` | 写入 useAppStore.appInstanceId |
| 12 | api.p2p.getMyDevices | `api.ts:1016-1024` | currentAppInstanceId 参数 |
| 13 | api.p2p.resolveCurrentPcClientId | `api.ts:1026-1035` | 解析当前 PC 的 pc_client_id |
| 14 | AddAndroidModal | `AddAndroidModal.tsx:63,222` | resolveCurrentPcClientId(appInstanceId) |
| 15 | AddLinuxVMUserModal | `AddLinuxVMUserModal.tsx:49,80` | 同上 |
| 16 | update_cloud_token | `commands/auth.rs:21` | 登录时 set_ready() |

---

## 6. 关键数据流简图

```
┌──────────────┐     app_instance_id      ┌──────────────────┐
│  Tauri App   │ ────────────────────────►│  useAppStore      │
│  (Rust)      │     get_app_instance     │  appInstanceId   │
└──────┬───────┘                          └────────┬─────────┘
       │                                           │
       │ CloudBridgeConfig                          │ getMyDevices /
       ▼                                           │ resolveCurrentPcClientId
┌──────────────┐     x-app-instance-id    ┌────────▼─────────┐
│ Cloud Bridge │ ────────────────────────►│ Gateway          │
│ WebSocket    │                          │ DeviceRegistry   │
└──────────────┘                          └────────┬─────────┘
                                                   │
       ┌──────────────────────────────────────────┘
       │ get_device_by_app_instance_id
       ▼
┌──────────────────────────────────────────────────────────────┐
│ GET /api/p2p/my-devices?current_app_instance_id={id}         │
│ → devices[].is_local, by_app_instance[].is_local             │
└──────────────────────────────────────────────────────────────┘
```
