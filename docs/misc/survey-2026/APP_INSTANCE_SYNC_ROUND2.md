# App Instance 同步与失败场景（Round 2）

**输入**：`docs/survey-2026/APP_INSTANCE_ROUND1.md`、App.tsx、useAppStore、resolveCurrentPcClientId、DeviceRegistry

**产出日期**：2026-03-12

---

## 1. App 启动时 app_instance 获取时序

### 1.1 当前实现：非阻塞 useEffect

```typescript
// novaic-app/src/App.tsx (L81-88)
// 尽早获取 app_instance_id（Tauri 启动时即生成），供 my-devices、resolveCurrentPcClientId 等使用
useEffect(() => {
  invoke<{ app_instance_id: string }>('get_app_instance')
    .then((inst) => {
      if (inst?.app_instance_id) useAppStore.getState().patchState({ appInstanceId: inst.app_instance_id });
    })
    .catch(() => {});
}, []);
```

**关键点**：

- **非 await**：`useEffect` 内 `invoke` 为异步 fire-and-forget，不阻塞 App 渲染
- **执行时机**：App 首次 mount 后立即触发（依赖 `[]`）
- **与 restoreSession 并行**：两个 `useEffect` 同时运行，无先后保证

### 1.2 时序图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  App mount                                                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
         │
         ├── useEffect #1: get_app_instance
         │      │
         │      └── invoke('get_app_instance')  ──►  Tauri 读取 AppInstanceState
         │                │                              │
         │                │  (异步返回)                   │  app_instance_id 在 setup.rs 已生成
         │                ▼                              │  与 Cloud Bridge 无关
         │         patchState({ appInstanceId })         │
         │
         └── useEffect #2: restoreSession
                │
                └── getAccessToken() → update_cloud_token(token)
                           │
                           └── login_notify.notify_one()
                                    │
                                    └── Cloud Bridge 开始连接 (等待 login_notify 后)
                                              │
                                              └── WS 握手: x-app-instance-id → DeviceRegistry
```

### 1.3 竞态窗口

| 时间点 | appInstanceId (Store) | DeviceRegistry.app_instance_id |
|--------|----------------------|--------------------------------|
| T0: App mount | null | 空（Cloud Bridge 未连） |
| T1: get_app_instance 返回 | 已设置 | 仍空 |
| T2: 用户登录，Cloud Bridge 连接 | 已设置 | 已写入 |
| T3: 用户登录后立即点「添加 Android」 | 可能仍 null（若 T1 未完成） | 可能仍空（连接中） |

**结论**：`appInstanceId` 与 DeviceRegistry 的 `app_instance_id` 存在**双重异步**，无强一致保证。用户登录后快速操作 AddAndroidModal 时，可能遇到 `appInstanceId` 未同步或 Cloud Bridge 尚未完成握手的情况。

---

## 2. resolveCurrentPcClientId 失败场景

### 2.1 实现逻辑

```typescript
// novaic-app/src/services/api.ts (L1026-1035)
resolveCurrentPcClientId: async (appInstanceId: string | null): Promise<string | undefined> => {
  if (!appInstanceId) return undefined;
  try {
    const res = await api.p2p.getMyDevices(appInstanceId);
    const local = res.devices?.find((d) => d.is_local);
    return local?.device_id ?? local?.pc_client_id ?? res.devices?.[0]?.device_id;
  } catch {
    return undefined;
  }
},
```

### 2.2 失败场景分解

#### 场景 A：appInstanceId 未同步

| 条件 | 表现 |
|------|------|
| `appInstanceId === null` | 第一行直接 `return undefined` |
| 触发原因 | `get_app_instance` 尚未返回、invoke 失败（Web 模式/无 Tauri）、catch 吞掉错误 |

**代码路径**：`AddAndroidModal` / `AddLinuxVMUserModal` 从 `useAppStore(s => s.appInstanceId)` 取值，若为 null 则传入 `resolveCurrentPcClientId(null)` → 立即返回 undefined。

#### 场景 B：Cloud Bridge 未连接

| 条件 | 表现 |
|------|------|
| Cloud Bridge WS 未建立或刚断开 | `get_device_by_app_instance_id(current_app_instance_id)` 返回 `None` |
| 原因 | `app_instance_id` 仅在 Cloud Bridge **握手时** 通过 `x-app-instance-id` header 写入 DeviceRegistry |

**Gateway 侧逻辑**（`p2p.py` L405-406）：

```python
if current_app_instance_id.strip():
    dev = registry.get_device_by_app_instance_id(current_app_instance_id.strip())
    if dev:
        current_pc_client_id = dev.device_id
# 否则 current_pc_client_id = ""
```

若 `dev` 为 None，则 `current_pc_client_id = ""`，`_build_device_item` 中无人满足 `entry.device_id == current_pc_client_id`，故**所有 device 的 is_local 均为 false**。

**resolveCurrentPcClientId 行为**：`local` 为 undefined，退化为 `res.devices?.[0]?.device_id`。多 PC 时可能返回错误 PC；若 `devices` 为空则返回 undefined。

#### 场景 C：无 is_local（设备列表为空或本机未在列表中）

| 条件 | 表现 |
|------|------|
| `res.devices` 为空 | 用户无任何 P2P 注册设备，返回 `undefined` |
| `res.devices` 非空但无 is_local | Cloud Bridge 未连接（见场景 B）或本机 device_id 不在 P2P 注册表中 |

**Fallback 链**：`local?.device_id ?? local?.pc_client_id ?? res.devices?.[0]?.device_id`。多 PC 且无 is_local 时，会取第一个设备，可能误选。

### 2.3 失败场景汇总

| 场景 | 根因 | resolveCurrentPcClientId 结果 |
|------|------|-------------------------------|
| A: appInstanceId 未同步 | get_app_instance 未完成 / 失败 | `undefined` |
| B: Cloud Bridge 未连接 | app_instance_id 未写入 DeviceRegistry | 无 is_local；fallback 到 devices[0] 或 undefined |
| C: 无 is_local | Cloud Bridge 未连 / 本机未在 P2P 表 | fallback 到 devices[0] 或 undefined |

---

## 3. my-devices 中 is_local 标注的依赖链

### 3.1 依赖链

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  1. 前端传入 current_app_instance_id                                               │
│     (来自 useAppStore.appInstanceId ← get_app_instance)                            │
└─────────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  2. Gateway: registry.get_device_by_app_instance_id(current_app_instance_id)      │
│     - 遍历 DeviceRegistry._devices                                               │
│     - 匹配 d.app_instance_id == aid && d.is_connected                              │
└─────────────────────────────────────────────────────────────────────────────────┘
         │
         │  app_instance_id 来源？
         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  3. DeviceRegistry.app_instance_id 写入时机                                        │
│     - 仅当 Cloud Bridge WebSocket 握手时                                          │
│     - pc_client_websocket() 从 header 解析 x-app-instance-id                      │
│     - registry.connect(..., app_instance_id=app_instance_id)                      │
└─────────────────────────────────────────────────────────────────────────────────┘
         │
         │  Cloud Bridge 何时发送？
         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  4. Cloud Bridge connect_and_run()                                                │
│     - 从 AppInstanceState 读取 app_instance_id（与 get_app_instance 同源）         │
│     - 建立 WS 时设置 header: x-app-instance-id                                    │
│     - 需 login_notify 后才会连接（登录后）                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  5. current_pc_client_id = dev.device_id (若 get_device_by_app_instance_id 命中) │
│     _build_device_item(entry, registry, current_pc_client_id=...)                 │
│     → if entry.device_id == current_pc_client_id: item["is_local"] = True         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 依赖链小结

| 依赖项 | 说明 |
|--------|------|
| **Tauri AppInstance** | `app_instance_id` 在 setup 时生成，与 Cloud Bridge 无关 |
| **get_app_instance** | 前端通过 invoke 获取，写入 Store |
| **Cloud Bridge 连接** | 登录后 `login_notify` 触发，握手时携带 `x-app-instance-id` |
| **DeviceRegistry** | 握手时写入 `app_instance_id`，供 `get_device_by_app_instance_id` 查询 |
| **P2P 心跳** | `_p2p_registry` 有 device 才能出现在 my-devices；`is_local` 依赖 DeviceRegistry 的 `app_instance_id` 匹配 |

**断链点**：任一环节失败都会导致无 is_local 或错误标注。

---

## 4. AddAndroidModal、AddLinuxVMUserModal 对 pcClientId 的依赖

### 4.1 依赖关系

```typescript
// novaic-app/src/components/VM/AddAndroidModal.tsx
const appInstanceId = useAppStore((s) => s.appInstanceId);
// ...
const pcClientId = await api.p2p.resolveCurrentPcClientId(appInstanceId);
if (pcClientId === undefined) {
  throw new Error('请选择目标 PC 或确保 Tauri 应用已连接');
}
// 后续：api.devices.setup(device.id, ..., pcClientId)、api.devices.start(device.id, pcClientId)
```

```typescript
// novaic-app/src/components/VM/AddLinuxVMUserModal.tsx
const appInstanceId = useAppStore((s) => s.appInstanceId);
// ...
const pcClientId = await api.p2p.resolveCurrentPcClientId(appInstanceId);
if (pcClientId === undefined) {
  setProg({ phase: 'error', ..., error: '请选择目标 PC 或确保 Tauri 应用已连接' });
  return;
}
// 后续：api.devices.setup(device.id, ..., pcClientId)、api.devices.start(device.id, pcClientId)
```

### 4.2 使用场景

| Modal | 使用 pcClientId 的 API |
|-------|------------------------|
| AddAndroidModal | `api.devices.setup(device.id, undefined, pcClientId)`、`api.devices.start(device.id, pcClientId)` |
| AddLinuxVMUserModal | `api.devices.setup(device.id, { source_image, ... }, pcClientId)`、`api.devices.start(device.id, pcClientId)` |

**用途**：多 PC 场景下，指定在**当前 PC** 上执行 setup/start 等操作。若 `pcClientId` 错误，会发到其他 PC。

### 4.3 失败时的用户提示

两处 Modal 在 `resolveCurrentPcClientId` 返回 `undefined` 时均提示：

> **请选择目标 PC 或确保 Tauri 应用已连接**

该提示覆盖了：

- appInstanceId 未同步
- Cloud Bridge 未连接
- 设备列表为空

但未区分具体原因，用户难以自助排查。

### 4.4 依赖链小结

```
┌─────────────────────────────────────────────────────────────────┐
│  AddAndroidModal / AddLinuxVMUserModal                          │
│     │                                                            │
│     ├── useAppStore.appInstanceId  (可能为 null)                 │
│     │                                                            │
│     └── resolveCurrentPcClientId(appInstanceId)                  │
│            │                                                     │
│            ├── appInstanceId null → undefined                    │
│            └── getMyDevices(appInstanceId)                       │
│                   │                                               │
│                   └── Gateway 依赖 DeviceRegistry.app_instance_id │
│                          (Cloud Bridge 握手时写入)                │
│                                                                  │
│  失败 → 提示「请选择目标 PC 或确保 Tauri 应用已连接」            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 附录：代码索引

| 模块 | 路径 |
|------|------|
| App.tsx get_app_instance | `novaic-app/src/App.tsx` L81-88 |
| useAppStore appInstanceId | `novaic-app/src/application/store.ts` L100, L173 |
| resolveCurrentPcClientId | `novaic-app/src/services/api.ts` L1026-1035 |
| get_device_by_app_instance_id | `novaic-gateway/gateway/api/internal/pc_client.py` L157-165 |
| my-devices _build_device_item | `novaic-gateway/gateway/api/p2p.py` L369-388 |
| my-devices 端点 | `novaic-gateway/gateway/api/p2p.py` L393-346 |
| AddAndroidModal | `novaic-app/src/components/VM/AddAndroidModal.tsx` L63, L222-224 |
| AddLinuxVMUserModal | `novaic-app/src/components/VM/AddLinuxVMUserModal.tsx` L49, L80-84 |
| Cloud Bridge x-app-instance-id | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` L195-198 |
