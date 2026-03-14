# P2P 竞态修复 Round 1 设计：E2 RFB 不暴露 WebSocket Close Reason

**文档版本**: R1  
**创建时间**: 2026-03-12  
**关联缺口**: P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3 §3.4 E2

---

## 1. 问题陈述

### 1.1 背景

后端（VncProxy、vnc_bridge）在连接失败或异常时，通过 **WebSocket Close 帧** 发送具体错误信息，例如：

- `"PC offline or session expired"`（Relay 等待 PC 超时）
- `"Remote P2P connect failed: ..."`（relay/rendezvous 失败）
- `"VNC connection timed out (30s)"`（升级超时）
- `"VmControl P2P not ready yet — please wait a moment and retry"`（本地 P2P 未就绪）

这些 reason 由 `send_ws_close_with_reason`（vnc_proxy.rs:319）和 vnc_bridge（vnc_bridge.rs:161-165）正确发送。

### 1.2 问题

前端使用 **noVNC RFB** 的 `disconnect` 事件处理断开逻辑。经源码确认：

- RFB 的 `disconnect` 事件 `detail` 仅包含 `{ clean: boolean }`，**不包含 `reason`**
- WebSocket Close 的 `e.reason` 在 RFB 内部 `_socketClose(e)` 中仅用于日志，未转发到 `disconnect` 事件
- 前端 `useVnc.ts`、`vncStream.ts` 已预留 `e?.detail?.reason`，但该字段始终为空

**影响**：用户只能看到通用文案（如 "Connection lost, max retries exceeded"），无法看到后端返回的具体错误（如 "PC offline or session expired"），影响 P2P 竞态场景下的可诊断性与用户体验。

### 1.3 相关代码位置

| 层级 | 文件 | 说明 |
|------|------|------|
| 后端 | `vnc_proxy.rs:319-327` | `send_ws_close_with_reason` 发送 Close 帧 |
| 后端 | `vnc_bridge.rs:161-165` | 解析 CloseFrame.reason，emit 到前端 |
| 前端 | `vncBridge.ts:86-89` | `onclose?.({ reason: e.payload })` 传递 reason |
| 前端 | `useVnc.ts:112-134` | `e?.detail?.reason` 用于 setErrorMsg |
| 前端 | `vncStream.ts:198-219` | `e?.detail?.reason ?? e?.reason` 用于 notifySubscribers |
| noVNC | `rfb.js:710-742` | `_socketClose(e)` 接收 e.reason 但未转发 |
| noVNC | `rfb.js:980-984` | disconnect 事件仅 `detail: { clean }` |

---

## 2. 方案设计

### 2.1 方案对比

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A. 修改 noVNC 源码** | 在 rfb.js 中把 `e.reason` 写入 disconnect 的 detail | 改动集中、语义正确、上游可贡献 | 需维护 fork 或 patch |
| **B. WS 包装层** | 在 RFB 前加一层，拦截 raw channel 的 onclose，自行派发带 reason 的事件 | 不修改 noVNC | 需与 RFB 事件同步，易产生双事件或时序问题 |
| **C. 自定义协议** | 关闭前发送 JSON `{ type: 'error', message }` | 与 scrcpy 模式一致 | RFB 将 JSON 当 RFB 协议解析，会破坏连接 |
| **D. VncBridgeTransport 扩展** | 在 bridge 层 emit 独立 error 事件，前端监听 | 不改 noVNC | 仅覆盖 OTA 模式，直连 WebSocket 仍无 reason |

### 2.2 推荐方案：A. 修改 noVNC 源码（Patch）

**理由**：

1. 根因在 RFB 未将 WebSocket close reason 透传，在 RFB 内修复最直接
2. 改动小、风险可控，仅涉及 `_socketClose` 与 `_updateConnectionState` 的 disconnect 派发
3. 可向上游 noVNC 提交 PR，长期可回归官方版本
4. 同时覆盖 URL 直连与 VncBridgeTransport（raw channel）两种路径

### 2.3 noVNC 源码分析

**当前流程**（`@novnc/novnc` 1.5.0）：

```
WebSocket/rawChannel.onclose(e)
  → Websock._eventHandlers.close(e)   // websock.js:311-314
  → RFB._socketClose(e)              // rfb.js:286, 710
  → e.reason 仅用于 msg 日志
  → _updateConnectionState('disconnected')
  → dispatchEvent('disconnect', { detail: { clean } })  // 无 reason
```

**关键点**：

- `_socketClose(e)` 中 `e` 为标准 CloseEvent 或 `{ reason: string }`（VncBridgeTransport）
- `_fail(details)` 路径：`details` 为字符串（如 "Connection closed (code: 1011, reason: PC offline)"），也未进入 disconnect detail

### 2.4 具体修改（Patch 内容）

**位置 1**：`rfb.js` 在 `_socketClose` 中保存 reason：

```javascript
// _socketClose 开头，在 switch 之前
this._rfbCloseReason = (e && e.reason) ? String(e.reason) : '';
```

**位置 2**：`_fail` 中保存 reason（供非 socket close 的错误路径使用）：

```javascript
// _fail 内，在 _rfbCleanDisconnect = false 之后
this._rfbCloseReason = (typeof details === 'string') ? details : '';
```

**位置 3**：`_updateConnectionState` 中 disconnect 派发时加入 reason：

```javascript
// case 'disconnected': 的 dispatchEvent
this.dispatchEvent(new CustomEvent("disconnect", {
  detail: {
    clean: this._rfbCleanDisconnect,
    reason: this._rfbCloseReason || ''
  }
}));
```

**位置 4**：在 RFB 构造函数或 `_connect` 中初始化：

```javascript
this._rfbCloseReason = '';
```

### 2.5 实施方式

- **短期**：使用 `patch-package` 对 `@novnc/novnc` 打补丁，提交 `patches/@novnc+novnc@x.x.x.patch`
- **长期**：向 noVNC 提交 PR，合并后移除 patch

---

## 3. 接口变更

### 3.1 RFB disconnect 事件

| 变更 | 类型 | 说明 |
|------|------|------|
| `detail.reason` | 新增 | 字符串，WebSocket Close 的 reason 或 _fail 的 details |

**兼容性**：现有代码已使用 `e?.detail?.reason ?? ''`，新增字段为向后兼容。

### 3.2 前端

无需修改接口。`useVnc.ts`、`vncStream.ts` 已使用 `e?.detail?.reason`，patch 生效后即可获得值。

### 3.3 后端

无变更。`send_ws_close_with_reason` 与 vnc_bridge 已正确传递 reason。

---

## 4. 风险与回退

### 4.1 风险

| 风险 | 等级 | 缓解 |
|------|------|------|
| noVNC 升级后 patch 失效 | 中 | 升级时检查 patch 是否仍适用，必要时更新 |
| `_rfbCloseReason` 未初始化导致 undefined | 低 | 在构造函数中显式初始化 |
| 某些环境 e.reason 不可用 | 低 | 使用 `e?.reason` 和 `|| ''` 兜底 |

### 4.2 回退

1. 移除 `patch-package` 对 `@novnc/novnc` 的 patch
2. 执行 `npm install` 恢复原始依赖
3. 前端 `e?.detail?.reason` 会重新变为空，回退到当前通用错误文案，功能无破坏

---

## 5. 实施顺序

| 步骤 | 任务 | 产出 |
|------|------|------|
| 1 | 在 node_modules 中手动验证 patch 逻辑 | 确认 disconnect 能收到 reason |
| 2 | 使用 `patch-package` 生成 patch 文件 | `patches/@novnc+novnc@1.5.0.patch` |
| 3 | 在 package.json 的 postinstall 中启用 patch-package | 确保 CI/安装后自动打补丁 |
| 4 | 回归测试：OTA 模式、直连模式、P2P 失败场景 | 确认 "PC offline or session expired" 等可展示 |
| 5 | （可选）向 noVNC 提交 PR | 上游合并后移除 patch |

---

## 6. 参考文档

| 文档 | 关联内容 |
|------|----------|
| `P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md` | E2 缺口定义、错误传播路径 |
| `VNC_ERROR_HANDLING_AUDIT.md` | RFB 不暴露 close reason、前端 VNC 错误展示 |
| `novaic-app/src/hooks/useVnc.ts` | disconnect 处理、errorMsg 设置 |
| `novaic-app/src/services/vncStream.ts` | disconnect 处理、notifySubscribers error |
| `novaic-app/src/services/vncBridge.ts` | VncBridgeTransport onclose 传 reason |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | send_ws_close_with_reason |
| `novaic-app/src-tauri/src/commands/vnc_bridge.rs` | CloseFrame reason 转发 |
