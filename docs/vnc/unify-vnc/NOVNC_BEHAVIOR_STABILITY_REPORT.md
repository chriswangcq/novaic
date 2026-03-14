# noVNC 行为与 VNC 稳定性分析报告

> 研究范围：RFB 与 noVNC 行为对 VNC 稳定性的影响  
> 对照设计文档：`docs/expert-advance-for-unfiy-vnc.md`、`docs/unify-vnc/09-phase4-design-code-verification.md`  
> noVNC 版本：@novnc/novnc 1.5.0

---

## 一、disconnect 事件与 detail.clean

### 1.1 源码验证

**noVNC rfb.js 源码**（`node_modules/@novnc/novnc/lib/rfb.js`）：

```javascript
// L979-983: disconnected 状态时派发 disconnect 事件
case 'disconnected':
  this.dispatchEvent(new CustomEvent("disconnect", {
    detail: {
      clean: this._rfbCleanDisconnect
    }
  }));
```

**`_rfbCleanDisconnect` 语义**：

| 场景 | 值 | 触发路径 |
|------|-----|----------|
| 用户主动 `rfb.disconnect()` | `true` | disconnect() → disconnecting → _disconnect() → _sock.close() → _socketClose → disconnected，未经过 _fail |
| 服务端主动关闭连接 | `true` | _socketClose(state='connected') → disconnecting → disconnected |
| 连接错误、认证失败等 | `false` | _fail(details) 中显式设置 `_rfbCleanDisconnect = false` |

### 1.2 结论

**noVNC 会提供 `detail.clean`**，PHASE4 审计报告中的 P5（「可能无 detail.clean」）不成立。

- `e?.detail?.clean ?? false` 在正常断开时能得到 `true`
- 用户切换 Agent、组件 unmount 时主动断开，会得到 `clean: true`，不会误触发重连
- 异常断开（网络错误、认证失败）会得到 `clean: false`，会正确进入重连逻辑

### 1.3 潜在竞态（与 P6 相关）

transport 快速切换时，`doConnect` 内 `rfbRef.current.disconnect()` 会触发旧 RFB 的 disconnect 事件。此时 `detail.clean === true`，handler 会 `setStatus('disconnected')` 且不重连，行为正确。但 handler 中 `rfbRef.current = null` 可能与新 RFB 的赋值存在时序问题，建议保留 P6 的 connectId 或「若 rfbRef 已指向不同 RFB 则跳过」的防护逻辑。

---

## 二、credentialsrequired / securityfailure 与 RFB_OPTIONS

### 2.1 当前实现

| 位置 | credentialsrequired | securityfailure | RFB_OPTIONS.credentials |
|------|---------------------|-----------------|-------------------------|
| **useVnc** | ✅ 监听，`setStatus('failed')` + "VNC requires credentials (unexpected)" | ❌ 未监听 | 继承 `{}` |
| **vncStream** | ❌ 未监听 | ✅ 监听，`notifySubscribers(state, 'error', reason)` | 继承 `{}` |

**RFB_OPTIONS**（`types/vnc.ts`）：

```typescript
credentials: {},  // 始终为空
```

### 2.2 设计文档要求

`docs/expert-advance-for-unfiy-vnc.md` 3.2 节：

> credentials 根据设备配置决定（有密码则传，无则不传）

### 2.3 问题分析

1. **credentials 未按设备配置传入**：当前 `RFB_OPTIONS.credentials` 恒为 `{}`，若 VNC 服务端需要密码，会触发 `credentialsrequired`，而前端未从设备配置获取并传入 credentials。
2. **useVnc 将 credentialsrequired 视为「unexpected」**：设计上应支持有密码设备，此时 credentialsrequired 是预期行为，不应直接失败。
3. **vncStream 缺少 credentialsrequired**：若服务端需要认证，vncStream 不会处理 credentialsrequired，可能导致连接卡住或依赖 securityfailure 兜底。
4. **credentialsrequired vs securityfailure**：
   - `credentialsrequired`：需要认证但未提供或未提供完整 credentials
   - `securityfailure`：认证失败（密码错误等）

### 2.4 修复建议

1. **按设备配置传入 credentials**：在 `createVncTransport` 或调用 `useVnc`/`vncStream` 前，从设备配置读取 `vnc_password` 等，构造 `{ password: string }` 或 `{ username, password }` 传入 RFB options。
2. **useVnc**：在 credentialsrequired 时，若设备配置有密码，调用 `rfb.sendCredentials(creds)` 继续认证；若无，再 `setStatus('failed')`。
3. **vncStream**：增加 credentialsrequired 监听，逻辑与 useVnc 一致。
4. **RFB_OPTIONS**：保持 `credentials: {}` 作为默认值，实际 credentials 在创建 RFB 时按设备覆盖。

---

## 三、RFB 实例清理与 removeEventListener

### 3.1 disconnect 后 RFB 是否仍会触发事件

**noVNC 状态机**（rfb.js `_updateConnectionState`）：

- `disconnected` 为**终态**，`oldstate === 'disconnected'` 时直接 return，不再做状态迁移。
- 进入 disconnected 后：
  - `_sock.off('close')` 已调用，不再接收 socket 事件
  - `_rawChannel = null`，底层通道已释放
  - 理论上不会再有 connect/disconnect 等事件

### 3.2 事件监听器未移除的风险

1. **内存与引用**：监听器闭包持有 `setState`、`doConnect` 等，RFB 若被长期引用，会阻止组件和关联资源被 GC。
2. **边缘情况**：若 noVNC 未来或某路径在 disconnected 后仍派发事件，未移除的监听器会调用已卸载组件的 `setState`，可能产生 React 警告或异常。
3. **最佳实践**：在 `rfb.disconnect()` 前或 disconnect 回调中，对已注册的 `connect`、`disconnect`、`credentialsrequired` 等执行 `removeEventListener`。

### 3.3 修复建议

在 useVnc 和 vncStream 中，将监听器保存为具名引用，在 disconnect 或组件卸载时统一移除：

```typescript
// useVnc.ts 示例
const onConnect = () => { /* ... */ };
const onDisconnect = (e: Event & { detail?: { clean?: boolean } }) => { /* ... */ };
const onCredentialsRequired = () => { /* ... */ };

rfb.addEventListener('connect', onConnect);
rfb.addEventListener('disconnect', onDisconnect);
rfb.addEventListener('credentialsrequired', onCredentialsRequired);

// 在 disconnect 或 cleanup 中：
rfb.removeEventListener('connect', onConnect);
rfb.removeEventListener('disconnect', onDisconnect);
rfb.removeEventListener('credentialsrequired', onCredentialsRequired);
```

---

## 四、VncBridgeTransport 与 noVNC 兼容性

### 4.1 noVNC 对 raw channel 的要求

**Websock.attach**（websock.js L286-298）要求 raw channel 具备：

```javascript
["send", "close", "binaryType", "onerror", "onmessage", "onopen", "protocol", "readyState"]
```

**VncBridgeTransport** 实现情况：

| 属性 | 实现 | 说明 |
|------|------|------|
| send | ✅ | `send(data)` 通过 Tauri invoke 转发 |
| close | ✅ | 调用 `vnc_bridge_close`，清理监听，调用 `onclose` |
| binaryType | ✅ | `'arraybuffer'` |
| onerror, onmessage, onopen | ✅ | 可赋值 |
| protocol | ✅ | `''` |
| readyState | ✅ | CONNECTING/OPEN/CLOSING/CLOSED |

### 4.2 连接与断开流程

**建立连接**：

1. `new RFB(container, transport, options)` → `_connect()` → `_sock.attach(transport)`
2. Websock 将 `onopen`、`onclose`、`onmessage`、`onerror` 绑定到 transport
3. VncBridgeTransport 在 `connect()` 成功后调用 `this.onopen?.()`，触发 RFB 握手

**主动断开**：

1. `rfb.disconnect()` → `_disconnect()` → `_sock.close()`
2. Websock.close() 调用 `this._websocket.close()`，即 `VncBridgeTransport.close()`
3. VncBridgeTransport.close() 同步调用 `this.onclose?.({})`
4. Websock 的 close handler → RFB `_socketClose` → `disconnected` → 派发 disconnect 事件

**服务端/后端断开**：

1. Tauri 发送 `vnc_bridge:{bridgeId}:close` 事件
2. VncBridgeTransport 的 unlistenClose 调用 `this.onclose?.({ reason })`
3. 同上，进入 disconnect 流程

### 4.3 已知问题与注意事项

1. **断开检测**：依赖 Tauri 的 `vnc_bridge:close` 事件。若后端异常退出未发送该事件，前端可能无法及时感知断开。
2. **close 的同步性**：VncBridgeTransport.close() 同步调用 `onclose`，与 WebSocket 的异步 onclose 不同，但对 noVNC 的 Websock 兼容，无需改动。
3. **非 WebSocket 场景**：noVNC 对 WebSocket 兼容的 raw channel 支持完整，VncBridgeTransport 满足要求，未见明显兼容性问题。

---

## 五、问题汇总与修复优先级

| 编号 | 严重程度 | 描述 | 建议 |
|------|----------|------|------|
| C1 | 高 | credentials 未按设备配置传入，RFB_OPTIONS 恒为 `{}` | 从设备配置读取 vnc 密码，在创建 RFB 时传入 credentials |
| C2 | 高 | useVnc 将 credentialsrequired 一律视为失败 | 有设备密码时调用 sendCredentials，无密码时再失败 |
| C3 | 中 | vncStream 未监听 credentialsrequired | 增加 credentialsrequired 处理，与 useVnc 对齐 |
| C4 | 中 | RFB 事件监听器未 removeEventListener | 在 disconnect/cleanup 时移除所有监听器 |
| C5 | 低 | P6 竞态防护 | 在 disconnect handler 中增加「rfbRef 已指向不同 RFB 则跳过」的判断 |

---

## 六、结论

1. **disconnect detail.clean**：noVNC 会正确提供，当前 `e?.detail?.clean ?? false` 逻辑可用，无需修改。
2. **credentials**：与设计不符，需按设备配置传入，并正确处理 credentialsrequired。
3. **RFB 清理**：disconnect 后理论上不再派发事件，但建议在断开前移除监听器，避免潜在内存与 setState 问题。
4. **VncBridgeTransport**：满足 noVNC raw channel 要求，连接与断开流程正常，未发现明显兼容性问题。
