# VNC 稳定性研究：状态一致性与轮询

> 对照 `docs/unify-vnc/02-expert-design.md` §4.4、`docs/unify-vnc/09-phase4-design-code-verification.md` §2.7，研究 DeviceStatusStore、useDeviceStatusPolling、vncStream、reconnectVNCStream 的集成与状态一致性。

---

## 一、设计文档要求摘要

### 1.1 02-expert-design §4.4

- 使用 `DeviceStatusStore` 管理所有活跃设备状态
- 轮询间隔统一为 5s，**VNC 连接期间可降为 3s**（通过 store 的 subscription count 动态调整）

### 1.2 09-phase4-design-code-verification §2.7

| 检查项 | 设计 | 实现 | 结论 |
|--------|------|------|------|
| 轮询收敛 | 单一 store，无重复定时器 | ✅ useDeviceStatusPolling + DeviceStatusStore | 一致 |
| VNC 连接期间 | 轮询降为 3s | ✅ useVnc 中 incrementVnc/decrementVnc 通知 store | 一致 |
| DeviceFloatingPanel | 应订阅 store | ✅ useDeviceStatusPolling + useDeviceStatus | 已修复 |

**验证结论**：§2.7 仅基于 useVnc 路径做了验证，未考虑 **vncStream 路径**。

---

## 二、状态不一致点

### 2.1 DeviceStatusStore 与 vncStream 集成缺失

**现状**：

- `useVnc` 在 `status === 'connected'` 时调用 `incrementVncConnectionCount`，disconnect 时 `decrementVncConnectionCount`（`useVnc.ts` L151–157）
- `vncStream` (VNCViewShared) **完全不调用** `DeviceStatusStore` 的 `incrementVncConnectionCount` / `decrementVncConnectionCount`

**结论**：main 路径的 VNC 连接（vncStream）不会触发轮询降为 3s，导致 main 与 vm_user 的轮询间隔不一致。

| 路径 | 组件 | 是否调用 increment/decrement | 轮询间隔 |
|------|------|-----------------------------|----------|
| main | VNCViewShared (vncStream) | ❌ 否 | 5s |
| vm_user | DeviceDesktopView (useVnc) | ✅ 是 | 3s |

---

### 2.2 useDeviceStatusPolling 与 vncStream 的脱节

**实现**（`useDeviceStatusPolling.ts` L19–21）：

```ts
const intervalMs =
  vncConnectionCount > 0 ? POLL_CONFIG.VM_STATUS_FAST_INTERVAL : POLL_CONFIG.VM_STATUS_NORMAL_INTERVAL;
```

- `vncConnectionCount > 0` → 3s（`VM_STATUS_FAST_INTERVAL`）
- 否则 → 5s（`VM_STATUS_NORMAL_INTERVAL`）

**问题**：vncStream 连接时 `vncConnectionCount` 未增加，DeviceFloatingPanel 的 main 设备状态轮询仍是 5s。即使 main 已连接 VNC，轮询仍为 5s，与设计文档「VNC 连接期间降为 3s」不符。

---

### 2.3 vncStream retryCount 与 useVnc retryCountRef 独立

| 来源 | 变量 | 最大重试次数 | 重置时机 |
|------|------|------------|----------|
| useVnc | retryCountRef | 5 | connect 成功时 |
| vncStream | state.retryCount | 3 | connect 成功时 |
| vncStream | state.retryCount | 3 | reconnectVNCStream 时 |

**问题**：

1. 两个路径的重试上限不同（5 vs 3），行为不一致
2. 若 vncStream 重试 3 次失败，用户点「Start VM」会调用 `reconnectVNCStream(streamKey)`，此时 `reconnectVNCStream` **会重置** `retryCount`（见下节），因此用户可重新获得 3 次重试机会
3. 重试耗尽后，两个路径的 UI 状态不同步：useVnc 显示 `failed`；vncStream 显示 `error`，且「Start VM」按钮会触发 reconnectVNCStream，重置 retryCount

---

### 2.4 reconnectVNCStream 实现分析

**实现**（`vncStream.ts` L446–452）：

```ts
export function reconnectVNCStream(agentId: string) {
  const state = streams.get(agentId);
  if (state) {
    state.retryCount = 0;           // ✅ 重置 retryCount
    disconnectStream(agentId);     // ✅ 会清除 transportOrUrl
    setTimeout(() => connectStream(agentId), 100);  // ⚠️ 未传入 deviceId
  }
}
```

**disconnectStream**（L283–305）：

- 清除 `retryTimer`
- 停止 frame capture
- 断开 RFB
- 关闭 `transportOrUrl`（VncBridgeTransport 需显式 close）
- 设置 `transportOrUrl = null`

**结论**：

| 检查项 | 状态 |
|--------|------|
| 重置 retryCount | ✅ 是 |
| 清除 transportOrUrl | ✅ 是（disconnectStream 会） |
| 多 PC 时传入 deviceId | ❌ **否**：`connectStream(agentId)` 未传 deviceId |

**多 PC 问题**：`reconnectVNCStream` 的签名为 `(agentId: string)`，未接收 `deviceId`（pc_client_id）。`subscribeToVNCStream` 的第三参数 `deviceId` 会传给 `connectStream`，但 `StreamState` 未持久化。用户点击「Start VM」时，`reconnectVNCStream(streamKey)` 只传 streamKey，`connectStream(agentId)` 中 `deviceId` 为 `undefined`，`vmService.getVncTransport(agentId, undefined)` 可能路由到错误 PC。

---

## 三、vncStream 与 DeviceStatusStore 的集成缺失

| 缺失项 | 说明 |
|--------|------|
| incrementVncConnectionCount | vncStream 在 `status === 'connected'` 时未调用 |
| decrementVncConnectionCount | vncStream 在 disconnect 或 error 时未调用 |
| 状态持久化 | StreamState 未存储 `pcClientId`，reconnectVNCStream 无法恢复 |
| 重试策略统一 | vncStream 3 次 vs useVnc 5 次，建议统一 |

---

## 四、修复建议

### 4.1 高优先级：vncStream 接入 DeviceStatusStore

在 `vncStream.ts` 中：

1. **connect 成功**：在 `rfb.addEventListener('connect')` 回调中调用 `useDeviceStatusStore.getState().incrementVncConnectionCount()`
2. **disconnect / error**：在 `disconnectStream` 以及 `rfb.addEventListener('disconnect')` 中，在连接真正结束时调用 `decrementVncConnectionCount()`
3. 注意：vncStream 为模块级单例，需在 `connect` 时 increment，在 `disconnectStream` 或最后一个订阅者移除时 decrement，避免重复计数

**建议实现**：在 `StreamState` 的 `status` 从 `connected` 变为其他状态时 decrement；在 `status` 变为 `connected` 时 increment。与 useVnc 的 effect 逻辑一致。

### 4.2 高优先级：reconnectVNCStream 支持多 PC

1. **方案 A**：在 `StreamState` 中增加 `pcClientId?: string`，在 `subscribeToVNCStream` 时写入
2. **方案 B**：扩展 `reconnectVNCStream(agentId: string, deviceId?: string)`，由调用方传入

**推荐**：方案 A + 方案 B 结合。StreamState 持久化 `pcClientId`，reconnectVNCStream 优先使用 state 中的值，同时支持可选参数覆盖。

### 4.3 中优先级：统一重试策略

- 将 vncStream 的 `MAX_RETRIES` 从 3 改为 5，与 useVnc 一致
- 或抽取为共享配置（如 `WS_CONFIG.VNC_MAX_RETRIES`）

### 4.4 低优先级：验证与文档更新

- 在 09-phase4-design-code-verification §2.7 中补充：vncStream 路径需接入 DeviceStatusStore
- 在 02-expert-design 中注明：vncStream 作为 createVncTransport 共享模式（P4-17）完成前，main 路径需单独接入

---

## 五、总结

| 问题 | 影响 | 建议 |
|------|------|------|
| vncStream 未调用 increment/decrement | main 路径轮询仍为 5s，与 vm_user 不一致 | 在 vncStream 中接入 DeviceStatusStore |
| reconnectVNCStream 未传 deviceId | 多 PC 时可能路由错误 | 持久化 pcClientId 或扩展签名 |
| retryCount 独立且上限不同 | 行为不一致，用户体验差异 | 统一为 5 次 |

**核心结论**：09-phase4 设计文档 §2.7 的「VNC 连接期间轮询降为 3s」仅对 useVnc 路径成立。DeviceFloatingPanel 的 main 分支使用 VNCViewShared（vncStream），未接入 DeviceStatusStore，导致 main 与 vm_user 的轮询间隔不一致，需修复。
