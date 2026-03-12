# vncStream 与 createVncTransport 双轨差异报告

> 研究范围：DeviceFloatingPanel main 使用 VNCViewShared（vncStream）与设计要求的 createVncTransport 统一路径之间的稳定性差异。

---

## 一、双轨差异总览

| 维度 | vncStream（VNCViewShared / main） | createVncTransport + useVnc（DeviceDesktopView） |
|-----|----------------------------------|--------------------------------------------------|
| **传输获取** | `vmService.getVncTransport(agentId, deviceId)` | `createVncTransport(VncTarget)` |
| **前端探测** | 非 OTA 时 `testWebSocket(url)` 探测 | 无探测，直接建立 RFB |
| **重连次数** | 最多 3 次 | 最多 5 次 |
| **重连延迟** | 固定 2s（disconnect）或 3s（catch） | 指数退避：2s × 2^n |
| **状态机** | `disconnected \| connecting \| connected \| error` | `connecting \| connected \| disconnected \| reconnecting \| failed` |
| **frame capture** | 隐藏 div + RFB，100ms 复制到共享 canvas | 无，RFB 直接渲染到可见容器 |
| **使用场景** | DeviceFloatingPanel main、缩略图↔全屏共享 | DeviceDesktopView（vm_user、main 全屏） |

---

## 二、逐项分析

### 2.1 testWebSocket 与设计 §3.3 的冲突

**设计文档 §3.3（expert-advance-for-unfiy-vnc.md）**：

> 取消前端的 WebSocket 探测，改为依赖后端的 `ensure_vnc_endpoint` 返回。传输层建立时如果后端 endpoint 还没 ready，WebSocket 连接会被后端 hold 住或拒绝。前端只需要处理连接失败然后重试，不需要额外的探测步骤。

**vncStream 现状**（`vncStream.ts:142-148`）：

```typescript
// 非 OTA 时测试 WebSocket 可用性（OTA 下 getVncTransport 已建立连接）
if (typeof state.transportOrUrl === 'string') {
  const wsAvailable = await testWebSocket(state.transportOrUrl);
  if (!wsAvailable) {
    state.transportOrUrl = null;
    throw new Error('VNC WebSocket not available');
  }
}
```

**结论**：vncStream 的 `testWebSocket` 与设计 §3.3 明确冲突。

**探测失败时行为**：

- 抛出 `'VNC WebSocket not available'`，进入 catch 分支
- `state.status = 'error'`，`state.transportOrUrl = null`
- 若有订阅者且 `retryCount < 3`，3 秒后重试 `connectStream`
- 探测超时使用 `WS_CONFIG.CONNECTION_TIMEOUT`（30s），与后端 P2P/relay 对齐，但探测本身增加一次完整 WebSocket 往返，延迟较高

**createVncTransport 路径**：无探测，直接 `new RFB(container, transport, opts)`，符合设计。

---

### 2.2 重连策略差异

| 项目 | vncStream | useVnc |
|------|-----------|--------|
| 最大重试 | 3 次 | 5 次 |
| 延迟策略 | 固定 2s（disconnect）或 3s（catch） | 指数退避：2s, 4s, 8s, 16s, 32s |
| 触发条件 | `state.subscribers.size > 0 && retryCount < 3` | `!clean && retryCount < MAX_RETRIES` |

**稳定性影响**：

- main 连接（vncStream）在 3 次失败后即放弃，而 vm_user（useVnc）可重试 5 次
- 固定 2s 在短暂网络波动时可能过于激进；指数退避可减轻瞬时故障压力
- **结论**：main 路径更容易过早放弃连接，稳定性弱于 vm_user 路径

---

### 2.3 状态机与 UX 差异

| vncStream | useVnc | 语义 |
|-----------|--------|------|
| `disconnected` | `disconnected` | 未连接 / 正常断开 |
| `connecting` | `connecting` | 首次连接中 |
| `connected` | `connected` | 已连接 |
| `error` | `reconnecting` | 非 clean 断开，正在重试 |
| — | `failed` | 重试耗尽，最终失败 |

**UX 差异**：

- **reconnecting**：useVnc 在重试期间保持「重连中」状态，用户可见「正在重试」提示
- **error**：vncStream 在首次连接失败或重试耗尽后统一为 `error`，无「重连中」中间态
- vncStream 的 `error` 既可能是「首次失败」也可能是「3 次重试后放弃」，语义混合

---

### 2.4 frame capture 与 attachVNCContainer

**vncStream 机制**：

1. 创建隐藏 div（`left: -9999px`），RFB 渲染到其内部 canvas
2. 每 100ms 将 RFB 的 `_canvas` 复制到共享 `state.canvas`
3. 订阅者（VNCViewShared）通过 `onFrame` 收到共享 canvas，再 `drawImage` 到本地 canvas
4. 全屏时 `attachVNCContainer(streamKey, container)` 将 RFB 容器 `appendChild` 到可见父元素

**attachVNCContainer 实现**（`vncStream.ts:467-478`）：

```typescript
export function attachVNCContainer(agentId: string, parent: HTMLElement): boolean {
  const state = streams.get(agentId);
  if (!state?.rfbContainer) return false;
  state.rfbContainer.style.position = 'relative';
  state.rfbContainer.style.left = '0';
  state.rfbContainer.style.top = '0';
  parent.appendChild(state.rfbContainer);
  if (state.rfb) state.rfb.focus();
  return true;
}
```

**连接抖动分析**：

- `appendChild` 仅移动 DOM 节点，不重建 RFB 或 WebSocket
- WebSocket 连接与 DOM 位置无关，移动容器不会触发断开
- `detachVNCContainer` 同理，仅将容器移回 body 并隐藏
- **结论**：attach/detach 过程中**不会**产生连接抖动

**潜在问题**：

- 缩略图↔全屏切换时，`status` 变化会触发 effect 的 attach/detach
- 若 `status` 在 `connected` 附近短暂波动，可能多次 attach/detach，造成视觉闪烁，但不会断开连接

---

## 三、稳定性影响汇总

| 影响项 | 严重程度 | 说明 |
|--------|----------|------|
| testWebSocket 与设计冲突 | 中 | 增加一次探测往返，存在探测成功但 RFB 连接失败的时序窗口 |
| main 重试次数少 | 高 | 3 次 vs 5 次，main 更易放弃 |
| 固定重连延迟 | 中 | 2s/3s 固定，网络波动时可能过于频繁 |
| 状态机语义混合 | 低 | error 语义不清晰，影响错误提示与调试 |
| attachVNCContainer 抖动 | 无 | DOM 移动不触发重连 |

---

## 四、统一建议

### 4.1 短期（vncStream 保留时）

1. **移除 testWebSocket**：与设计 §3.3 对齐，非 OTA 时直接建立 RFB，失败由重试处理
2. **统一重连参数**：将 vncStream 重试改为 5 次、指数退避（与 `WS_CONFIG.VNC_RETRY_DELAY_MS`、`VNC_MAX_RETRIES` 一致）
3. **增加 reconnecting 状态**：在重试期间使用 `reconnecting`，与 useVnc 一致

### 4.2 中期（设计目标）

1. **迁移 DeviceFloatingPanel main 到 createVncTransport + useVnc**
   - 需解决共享流：缩略图与全屏共享同一连接
   - 方案 A：在 `createVncTransport` 层做连接复用（引用计数 + 共享 transport）
   - 方案 B：用 `VncCanvas` + 共享 transport 的 hook，由上层管理复用

2. **废弃 vmService.getVncTransport**：统一使用 `createVncTransport(VncTarget)`，并添加 `@deprecated` 注释

### 4.3 代码修改优先级

| 优先级 | 修改项 | 文件 |
|--------|--------|------|
| P0 | 移除 testWebSocket 调用 | `vncStream.ts` |
| P1 | vncStream 重试改为 5 次 + 指数退避 | `vncStream.ts` |
| P2 | vncStream 增加 reconnecting 状态 | `vncStream.ts`, `VNCViewShared.tsx` |
| P3 | DeviceFloatingPanel main 迁移到 createVncTransport | `DeviceFloatingPanel.tsx`, 新建共享流层 |

---

## 五、附录：关键代码引用

- `vncStream` 探测：`novaic-app/src/services/vncStream.ts:142-148`
- `testWebSocket` 实现：`novaic-app/src/services/vncStream.ts:262-280`
- vncStream 重连：`novaic-app/src/services/vncStream.ts:216-224, 249-256`
- useVnc 重连：`novaic-app/src/hooks/useVnc.ts:116-122`
- 设计 §3.3：`docs/expert-advance-for-unfiy-vnc.md:99-104`
- DeviceFloatingPanel main 使用：`novaic-app/src/components/Layout/DeviceFloatingPanel.tsx:296`
