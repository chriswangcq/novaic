# 第三轮调研（深层）：app_instance 同步与失败场景

> 调研目标：app_instance 同步时机、Cloud Bridge 未连接时的 is_local、多窗口/多标签共享、失败场景与降级行为。

---

## 1. 前端 appInstanceId 与 Tauri 的同步时机

### 1.1 时序概览

```
Tauri 启动
  ├─ setup_shared() → AppInstance::new_desktop() → app_instance_id 立即可用
  ├─ app.manage(app_instance) → 注入 Tauri State
  └─ lib.rs spawn → VmControl.start(CloudBridgeConfig{ app_instance_id }) → Cloud Bridge 等待 login_notify

用户登录 (isSignedIn = true)
  └─ App.tsx useEffect 触发
       ├─ invoke('get_app_instance').then(...)  ← 异步、无 await
       ├─ pushToken() → update_cloud_token → login_notify.notify_one()
       └─ getAgentService().initialize()
```

### 1.2 同步实现（App.tsx:203-208）

```typescript
// P2-5: 尽早获取 app_instance_id（Tauri 启动时即生成），供 my-devices 等使用
invoke<{ app_instance_id: string }>('get_app_instance')
  .then((inst) => {
    if (inst?.app_instance_id) useAppStore.getState().patchState({ appInstanceId: inst.app_instance_id });
  })
  .catch(() => {});
```

| 属性 | 说明 |
|------|------|
| **触发条件** | `isSignedIn === true` 后 useEffect 执行 |
| **调用方式** | fire-and-forget（无 await，与 pushToken 并行） |
| **延迟风险** | 存在：invoke 为异步，store 更新在 .then() 回调中完成 |

### 1.3 可能延迟的场景

| 场景 | 延迟原因 | 影响 |
|------|----------|------|
| **登录后立即操作** | 用户登录后立刻打开 AddAndroidModal / AddLinuxVMUserModal，在 get_app_instance 返回前点击「创建」 | `appInstanceId` 仍为 null，`resolveCurrentPcClientId(null)` 返回 undefined |
| **invoke 排队** | Tauri 主线程繁忙时，get_app_instance 响应可能延迟数十毫秒 | 同上 |
| **Tauri 未就绪** | 极端情况：WebView 已渲染但 Tauri 命令尚未注册 | invoke 抛错，.catch() 吞掉，appInstanceId 保持 null |

### 1.4 调用方依赖

| 调用方 | 读取方式 | 若 appInstanceId 为 null |
|--------|----------|--------------------------|
| `AddAndroidModal` | `useAppStore(s => s.appInstanceId)` | `resolveCurrentPcClientId(null)` → undefined → 抛错「请选择目标 PC 或确保 Tauri 应用已连接」 |
| `AddLinuxVMUserModal` | 同上 | 同上 |
| `api.p2p.getMyDevices(currentAppInstanceId)` | 参数传入 | 不传 current_app_instance_id，my-devices 无 is_local |
| `api.p2p.resolveCurrentPcClientId(appInstanceId)` | 参数传入 | 直接 return undefined（api.ts:1027） |

### 1.5 结论：是否可能延迟？

**是，存在延迟可能。** 前端 appInstanceId 的写入依赖异步 invoke 完成，与用户操作无强顺序保证。典型窗口期：登录后 0～100ms 内，store 可能尚未更新。

---

## 2. Cloud Bridge 未连接时 my-devices 的 is_local 标注

### 2.1 数据流依赖

```
is_local 标注链：
  current_app_instance_id (调用方传入)
    → registry.get_device_by_app_instance_id(app_instance_id)
    → 需 DeviceRegistry 中存在该 app_instance_id 且 is_connected
    → DeviceRegistry 数据来源：Cloud Bridge WebSocket 连接时 x-app-instance-id header
```

### 2.2 DeviceRegistry 映射建立时机

| 步骤 | 位置 | 说明 |
|------|------|------|
| 1 | `cloud_bridge.rs:189-192` | WebSocket 握手时设置 `x-app-instance-id` header |
| 2 | `pc_client.py` WebSocket 接受 | 读取 header，调用 `registry.connect(..., app_instance_id=...)` |
| 3 | `DeviceState` | 存储 `app_instance_id`，`is_connected` 由 `ws is not None` 决定 |

**Cloud Bridge 连接前提**：`login_notify` 触发（用户登录后 `update_cloud_token` 调用），且 `cloud_token` 非空。

### 2.3 get_device_by_app_instance_id 约束

```python
# pc_client.py:153-161
def get_device_by_app_instance_id(self, app_instance_id: str) -> Optional[DeviceState]:
    if not app_instance_id or not app_instance_id.strip():
        return None
    aid = app_instance_id.strip()
    for d in self._devices.values():
        if d.app_instance_id == aid and d.is_connected:  # ← 必须 is_connected
            return d
    return None
```

### 2.4 Cloud Bridge 未连接时的行为

| 状态 | 结果 |
|------|------|
| **Cloud Bridge 从未连接** | DeviceRegistry 无该 device_id 的 app_instance_id，或该 device 不在 _devices 中 |
| **Cloud Bridge 已断开** | `d.is_connected` 为 False，`get_device_by_app_instance_id` 返回 None |
| **Gateway 返回** | `current_pc_client_id = ""`，`_build_device_item` 中 `current_pc_client_id and entry.device_id == ...` 恒为 False |
| **is_local** | **所有设备均无 is_local 标注** |

### 2.5 典型未连接场景

| 场景 | 说明 |
|------|------|
| 用户刚登录，Cloud Bridge 尚未连上 | 连接建立需数秒，此期间 my-devices 无 is_local |
| 网络抖动导致 WebSocket 断开 | 重连前（默认 5s 重试）is_local 失效 |
| JWT 过期且未刷新 | Cloud Bridge 可能断开，直至 token 更新 |
| 移动端无 Cloud Bridge | 移动端架构不同，通常不运行 VmControl，无 Cloud Bridge |

### 2.6 结论

**Cloud Bridge 未连接时，my-devices 的 is_local 无法标注。** 所有设备项均无 `is_local` 字段，`by_app_instance` 中对应楼层也无 `is_local`。

---

## 3. 多窗口/多标签场景下 app_instance 的共享

### 3.1 Tauri 架构

| 维度 | 说明 |
|------|------|
| **进程模型** | 单进程：Tauri 主进程 + 内嵌 WebView |
| **AppInstance** | `setup_shared` 中创建一次，`app.manage(app_instance)` 注入，全进程共享 |
| **窗口配置** | `tauri.conf.json` 仅配置 `main` 单窗口，`withGlobalTauri: true` |

### 3.2 app_instance 共享范围

| 层级 | 共享情况 |
|------|----------|
| **Tauri 主进程** | 单一 `AppInstanceState`，所有 Tauri 命令（get_app_instance、get_vnc_proxy_url 等）读同一实例 |
| **多 WebView 窗口** | 若 Tauri 创建多窗口，每个窗口的 invoke 均发往同一主进程，共享同一 app_instance_id |
| **同一窗口内多 React 组件** | 共享 `useAppStore.appInstanceId`（Zustand 单例） |

### 3.3 多标签（Browser Tabs）

当前为 **Tauri 桌面应用**，前端运行在 WebView 内，**无浏览器多标签**。若未来支持「在系统浏览器中打开」等能力，需另行考虑：

- 浏览器标签：每个标签独立 JS 上下文，但若通过 Tauri 的 `invoke` 访问后端，仍会命中同一 Tauri 进程，得到相同 app_instance_id。
- 多开应用实例：用户启动多个 NovAIC 进程（如从不同工作目录启动），则每个进程有独立 app_instance_id，不共享。

### 3.4 结论

**单进程内多窗口/多组件共享同一 app_instance_id。** 不存在「同一进程内不同窗口有不同 app_instance」的情况。

---

## 4. app_instance 失败场景 + 降级行为

### 4.1 失败场景汇总

| # | 场景 | 触发条件 | 表现 |
|---|------|----------|------|
| F1 | **前端 appInstanceId 未同步** | 登录后极短时间内操作（如立刻打开 Modal 并提交） | store 中 appInstanceId 为 null |
| F2 | **get_app_instance invoke 失败** | Tauri 未就绪、权限问题、命令未注册 | .catch() 吞错，appInstanceId 保持 null |
| F3 | **Cloud Bridge 未连接** | 刚登录、网络断开、JWT 过期、重连中 | DeviceRegistry 无映射或 is_connected=False |
| F4 | **未传 current_app_instance_id** | 前端调用 getMyDevices() 不传参、或传 null | Gateway 侧 current_pc_client_id=""，无 is_local |
| F5 | **P2P 与 DeviceRegistry 不同步** | P2P 心跳有 device 但 Cloud Bridge 未连，或反之 | 设备列表不完整或无法匹配 is_local |
| F6 | **多 PC 且无 is_local** | 用户有多台 PC，Cloud Bridge 未连或传参缺失 | 无法区分「本机」与「远端」，可能选错目标 PC |

### 4.2 各调用方的降级行为

| 调用方 | 正常行为 | 降级行为 | 代码位置 |
|--------|----------|----------|----------|
| **resolveCurrentPcClientId** | 传 appInstanceId，取 is_local 设备，否则取第一个 | appInstanceId 为 null → 直接 return undefined；is_local 全无时 → 取 `devices[0]` | api.ts:1026-1032 |
| **get_vnc_proxy_url** | 从 AppInstanceState 读 app_id，传 my-devices | app_id 为空时 path 不带 query；取第一个 online 设备 | vnc_urls.rs:43-56 |
| **get_scrcpy_proxy_url** | 同上 | 同上 | vnc_urls.rs:99-112 |
| **vnc_bridge_connect** | 同上 | 同上 | vnc_bridge.rs:52-68 |
| **AddAndroidModal** | resolveCurrentPcClientId 成功 → 用 pcClientId 创建 | 返回 undefined → 抛错「请选择目标 PC 或确保 Tauri 应用已连接」 | AddAndroidModal.tsx:222-224 |
| **AddLinuxVMUserModal** | 同上 | 同上 | AddLinuxVMUserModal.tsx:80-82 |

### 4.3 降级行为详解

#### resolveCurrentPcClientId（api.ts）

```typescript
resolveCurrentPcClientId: async (appInstanceId: string | null): Promise<string | undefined> => {
  if (!appInstanceId) return undefined;  // 降级 1：无 appInstanceId 直接失败
  try {
    const res = await api.p2p.getMyDevices(appInstanceId);
    const local = res.devices?.find((d) => d.is_local);
    return local?.device_id ?? local?.pc_client_id ?? res.devices?.[0]?.device_id;  // 降级 2：无 is_local 时取第一个
  } catch {
    return undefined;  // 降级 3：请求失败
  }
},
```

| 降级层级 | 条件 | 结果 |
|----------|------|------|
| 1 | appInstanceId 为 null | 直接 undefined，无网络请求 |
| 2 | 有 appInstanceId 但无 is_local | 使用第一个设备（可能非本机） |
| 3 | getMyDevices 抛错 | undefined |

#### Rust 侧（get_vnc_proxy_url / vnc_bridge_connect）

- **app_id 为空**：请求 `/api/p2p/my-devices` 不带 `current_app_instance_id`，Gateway 不标 is_local。
- **取第一个 online**：无论 is_local 是否存在，均取 `arr.iter().find(|e| e.get("online")...)`，即第一个在线设备。

### 4.4 潜在问题

| 问题 | 说明 |
|------|------|
| **单 PC 用户** | 降级 2 取第一个设备通常正确，影响小 |
| **多 PC 用户** | 无 is_local 时可能选到远端 PC，导致 setup/start 发往错误机器 |
| **前端快速操作** | appInstanceId 未同步时 resolveCurrentPcClientId 直接失败，用户看到「请选择目标 PC」 |
| **静默失败** | get_app_instance 的 .catch(() => {}) 不报错，用户无感知，只能依赖后续操作失败推断 |

### 4.5 改进建议（可选）

| 建议 | 说明 |
|------|------|
| **await get_app_instance** | 在 pushToken 之后或并行时 await，确保 store 写入后再继续初始化 |
| **重试/轮询** | resolveCurrentPcClientId 在 appInstanceId 为 null 时，可先 invoke('get_app_instance') 再重试一次 |
| **UI 提示** | appInstanceId 为 null 时，Modal 提示「正在获取设备信息，请稍候」而非直接报错 |
| **Gateway 降级** | 当 get_device_by_app_instance_id 失败时，若仅有一台设备，可考虑默认标 is_local（需评估安全与语义） |

---

## 5. 附录：关键代码索引

| 主题 | 文件 | 行号/说明 |
|------|------|-----------|
| 前端 appInstanceId 同步 | `novaic-app/src/App.tsx` | 203-208 |
| resolveCurrentPcClientId | `novaic-app/src/services/api.ts` | 1026-1034 |
| get_device_by_app_instance_id | `novaic-gateway/gateway/api/internal/pc_client.py` | 153-161 |
| my-devices is_local 逻辑 | `novaic-gateway/gateway/api/p2p.py` | 344-355, 317-318 |
| AppInstance 创建 | `novaic-app/src-tauri/src/setup.rs` | 53-60 |
| Cloud Bridge header | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | 189-192 |
| AddAndroidModal 使用 | `novaic-app/src/components/VM/AddAndroidModal.tsx` | 63, 222-224 |
