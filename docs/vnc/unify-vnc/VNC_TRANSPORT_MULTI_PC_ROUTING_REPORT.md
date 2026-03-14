# VNC 传输层与多 PC 路由研究报告

> 对照 `docs/unify-vnc/02-expert-design.md` §3.2、`docs/unify-vnc/03-maindesk-vs-subuser.md`，追踪 device_id / pc_client_id 在 VNC 连接与多 PC 路由中的传递路径。

---

## 一、问题列表

| # | 问题 | 严重性 | 位置 |
|---|------|--------|------|
| 1 | **reconnectVNCStream 不传 deviceId** | 高 | `vncStream.ts` L447-453 |
| 2 | **StreamState 不持久化 deviceId** | 高 | `vncStream.ts` L23-35 |
| 3 | **device.pc_client_id 可能为空** | 中 | 依赖 Gateway `devices` 表与 `pc_client_id` 列填充 |
| 4 | **vnc_proxy 路径参数命名易混淆** | 低 | `vnc_proxy.rs` 路由参数 `device_id` 实为 `pc_client_id` |

---

## 二、路由路径追踪

### 2.1 vnc_proxy.rs — URL 结构与 P2P 路由

**URL 结构**（与设计一致）：

```
ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}
```

- `device_id`（路径参数）**实为 pc_client_id**（物理 PC 标识，VmControl Ed25519 hex）
- `agent_id`（路径参数）**即 resource_id**：maindesk 为 `device_id`，subuser 为 `{device_id}:{username}`

**路由逻辑**：

```rust
// route_vnc: device_id 用于本机判断与 P2P 目标
local_id.as_deref() == Some(device_id)  → serve_local_vnc (QUIC loopback)
else                                     → serve_remote_vnc (P2pClient::connect)
```

**P2pClient::connect 传参**：

```rust
// get_or_create_remote_conn(device_id, state)
state.p2p_client.connect(&gateway_url, &token, device_id)
```

- `device_id` 正确传入 `P2pClient::connect`，作为 `target_device_id` 用于 Gateway locate 与 relay 路由
- relay 层使用该 ID 定位目标 VmControl 实例

**结论**：vnc_proxy 后端对 `device_id`（pc_client_id）的使用正确，多 PC 时能正确路由到目标物理机。

---

### 2.2 vnc_urls.rs / get_vnc_proxy_url — Tauri 命令层

**参数**：

- `agentId`：resource_id（maindesk 为 device_id，subuser 为 `{device_id}:{username}`）
- `deviceId`：可选，pc_client_id（目标 PC）

**解析逻辑**：

```rust
// 1. 桌面：优先 local_vmcontrol.device_id，否则 deviceId
// 2. 移动端：deviceId 或 my-devices 第一个 online 的 pc_client_id
let device_id = p.local_vmcontrol.read().await.as_ref()
    .map(|info| info.device_id.clone())
    .or(deviceId);

match device_id {
    Some(id) => id,
    None => {
        // 调用 my-devices，取第一个 online 的 pc_client_id
        ...
    }
}
```

**多 PC 场景**：

- 若前端传入 `deviceId`（pc_client_id），则直接使用
- 未传时：桌面用本机 `local_vmcontrol`，移动端用 my-devices 第一个在线设备
- 多 PC 时，若未传 `deviceId`，会错误地连到本机或第一个在线 PC，而非目标 PC

**结论**：Tauri 命令层逻辑正确，但依赖前端在所有调用路径中正确传入 `deviceId`。

---

### 2.3 vncStream — subscribeToVNCStream / connectStream

**调用链**：

```
subscribeToVNCStream(streamKey, subscriber, deviceId)
  → connectStream(agentId, deviceId)
    → vmService.getVncTransport(agentId, deviceId)
      → get_vnc_proxy_url(agentId, deviceId) 或 VncBridgeTransport(agentId, deviceId)
```

**正确传递**：

- `subscribeToVNCStream` 第三参 `deviceId` 传入 `connectStream`
- `connectStream` 传入 `vmService.getVncTransport(agentId, deviceId)`
- 自动重连（disconnect 回调）中 `connectStream(agentId, deviceId)` 使用闭包捕获的 `deviceId`

**问题 1：reconnectVNCStream 不传 deviceId**

```typescript
// vncStream.ts L447-453
export function reconnectVNCStream(agentId: string) {
  const state = streams.get(agentId);
  if (state) {
    state.retryCount = 0;
    disconnectStream(agentId);
    setTimeout(() => connectStream(agentId), 100);  // ❌ 未传 deviceId
  }
}
```

- 调用方：`VNCViewShared` 的 `startVm` 中 `reconnectVNCStream(streamKey)` 在 VM 启动后触发
- 影响：多 PC 时，重连会走 `deviceId=undefined`，fallback 到本机或第一个在线 PC，而非目标 PC

**问题 2：StreamState 不持久化 deviceId**

```typescript
// vncStream.ts L23-35
interface StreamState {
  rfb: RFB | null;
  // ...
  transportOrUrl: string | VncBridgeTransport | null;
  // ❌ 无 deviceId 字段
}
```

- 重连时无法从 state 恢复 deviceId
- 需依赖调用方传入，或扩展 state 持久化 deviceId

---

### 2.4 vm.ts — getVncTransport / getVncUrl

```typescript
// vm.ts L166-184
async getVncUrl(agentId: string, deviceId?: string): Promise<string> {
  const url = await invoke<string>('get_vnc_proxy_url', { agentId, deviceId });
  return url;
}
async getVncTransport(agentId: string, deviceId?: string): Promise<string | VncBridgeTransport> {
  if (shouldUseVncBridge()) {
    const transport = new VncBridgeTransport(agentId, deviceId);
    await transport.connect();
    return transport;
  }
  return this.getVncUrl(agentId, deviceId);
}
```

**结论**：`vm.ts` 正确传递 `agentId` 与 `deviceId` 到 Tauri 和 VncBridgeTransport。

---

### 2.5 VncBridgeTransport — OTA 模式 pcClientId 传递

```typescript
// vncBridge.ts L56-66
constructor(private agentId: string, private deviceId?: string) {}
async connect(): Promise<void> {
  this.bridgeId = await invoke<string>('vnc_bridge_connect', {
    agentId: this.agentId,
    deviceId: this.deviceId ?? null,
  });
  // ...
}
```

**vnc_bridge.rs**：

```rust
// vnc_bridge_connect(
//   agentId: String,
//   deviceId: Option<String>,  // 即 pc_client_id
// )
let device_id = resolve_device_id(..., deviceId).await?;
let ws_url = p.ws_url(&device_id, &agent_id);
```

- `resolve_device_id` 与 `get_vnc_proxy_url` 相同：local_vmcontrol / deviceId / my-devices 第一个在线
- `ws_url` 使用解析后的 `device_id` 构建 WebSocket URL

**结论**：OTA 模式下 `pcClientId` 正确从 `VncBridgeTransport` 传到 `vnc_bridge_connect`，再传到 vnc_proxy。

---

### 2.6 前端调用路径汇总

| 调用路径 | deviceId/pcClientId 来源 | 传递正确性 |
|----------|--------------------------|------------|
| **AgentDesktopView** | `useAgentDevice` → `vncTarget.pcClientId`（来自 `device?.pc_client_id`） | ✓ |
| **DeviceDesktopView** | `device.pc_client_id` 或 `props.pcClientId`（vm_user） | ✓ |
| **DeviceFloatingPanel** | `device.pc_client_id` → `VNCViewShared` | ✓ |
| **VNCViewShared** | `propPcClientId` → `subscribeToVNCStream(streamKey, subscriber, propPcClientId)` | ✓ |
| **VNCViewShared** | `reconnectVNCStream(streamKey)` 在 startVm 后 | ❌ 未传 deviceId |
| **vncTransport.createVncTransport** | `target.pcClientId` | ✓ |

---

## 三、VncTarget 与 pc_client_id 数据源

**useAgentDevice**：

```typescript
// useAgentDevice.ts L36-53
function bindingToVncTarget(binding: AgentDeviceBinding, device: Device | null): VncTarget {
  const pcClientId = device?.pc_client_id;
  if (subject_type === 'vm_user') {
    return { resourceId: `${device_id}:${subject_id}`, ..., pcClientId };
  }
  return { resourceId: device_id, ..., pcClientId };
}
```

**device.pc_client_id 来源**：

- `api.devices.get(device_id)` 返回的 `Device`
- Gateway `DeviceResponse` 有 `pc_client_id: Optional[str]`
- Device 数据库表有 `pc_client_id` 列（`device.py` L117）

**风险**：若设备未关联或未正确设置 `pc_client_id`，则 `pcClientId` 为 `undefined`，多 PC 时 fallback 到本机或第一个在线 PC，可能路由错误。

---

## 四、修复建议

### 4.1 高优先级：reconnectVNCStream 支持 deviceId

**方案 A：扩展 reconnectVNCStream 签名**

```typescript
// vncStream.ts
export function reconnectVNCStream(agentId: string, deviceId?: string) {
  const state = streams.get(agentId);
  if (state) {
    state.retryCount = 0;
    disconnectStream(agentId);
    setTimeout(() => connectStream(agentId, deviceId), 100);
  }
}
```

**方案 B：StreamState 持久化 deviceId**

```typescript
interface StreamState {
  // ...
  deviceId?: string;  // 新增：首次连接时保存
}
// connectStream 中：state.deviceId = deviceId ?? state.deviceId;
// reconnectVNCStream 中：connectStream(agentId, state.deviceId);
```

**建议**：同时采用 A+B，保证：

1. 调用方显式传入 `deviceId` 时能正确重连
2. 自动重连时能从 state 恢复

**调用方修改**：`VNCViewShared` 的 `startVm` 中：

```typescript
reconnectVNCStream(streamKey, propPcClientId);
```

---

### 4.2 中优先级：StreamState 持久化 deviceId

在 `connectStream` 首次连接时保存：

```typescript
if (!state.deviceId && deviceId) {
  state.deviceId = deviceId;
}
```

并在 `disconnectStream` 中保留 `deviceId`（不清除），以便下次 `connectStream` 或 `reconnectVNCStream` 使用。

---

### 4.3 低优先级：vnc_proxy 路径参数命名

在 `vnc_proxy.rs` 路由参数处增加注释，避免混淆：

```rust
// 路径参数 device_id 实际为 pc_client_id（物理 PC 标识）
.route("/vnc/:device_id/:agent_id", get(vnc_handler))
```

或考虑未来将路径改为 `/vnc/:pc_client_id/:resource_id`（需前后端同步）。

---

### 4.4 数据完整性：确保 device.pc_client_id 填充

- 确认 Gateway `devices` 表与 `DeviceResponse` 中 `pc_client_id` 在设备创建/更新时正确写入
- 设备创建时需关联到正确的 `pc_client_id`（即运行 VmControl 的物理 PC）

---

## 五、总结

| 层级 | 状态 | 说明 |
|------|------|------|
| **vnc_proxy.rs** | ✓ | URL 使用 pc_client_id，P2pClient::connect 传参正确 |
| **vnc_urls.rs** | ✓ | agentId/deviceId 解析正确，依赖前端传参 |
| **vnc_bridge.rs** | ✓ | OTA 模式下 pc_client_id 正确传递 |
| **vm.ts** | ✓ | getVncTransport 和 getVncUrl 正确传参 |
| **vncTransport.ts** | ✓ | createVncTransport 使用 target.pcClientId |
| **vncStream** | ❌ | reconnectVNCStream 不传 deviceId；StreamState 持久化 deviceId |
| **VNCViewShared** | ⚠️ | subscribeToVNCStream 传 deviceId；reconnectVNCStream 不传 |

**核心修复**：在 `vncStream.ts` 中修复 `reconnectVNCStream` 的 deviceId 传递，并在 `StreamState` 中持久化 deviceId；在 `VNCViewShared` 的 `startVm` 中调用 `reconnectVNCStream(streamKey, propPcClientId)`。
