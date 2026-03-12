# VNC 连接失败问题分析报告

> 基于日志：后端全链路成功但 `send_count=0`，前端 RFB disconnect、Disconnection timed out、两次 connect、7577c885 在 89f7982b 建立后约 10ms 被 close

---

## 一、现象摘要

| 维度 | 现象 |
|------|------|
| **后端** | route_vnc_to_channel、open_vnc_stream、bridge_channel_quic、Tunnel、ensure_vnc_endpoint 全链路成功，无 ERROR |
| **后端异常** | `channel→quic 结束 rx 关闭 send_count=0` —— 前端从未向 channel 发送任何数据 |
| **前端** | RFB disconnect userInitiated=true、Disconnection timed out、创建 RFB 实例、close 调用 |
| **时间线** | 11:26:19 connect(7577c885) → 11:26:23 connect(89f7982b) → 11:26:23 close(7577c885) → 11:26:26 close(89f7982b) |

---

## 二、问题分析

### 2.1 为何 send_count=0？RFB 握手需要客户端先发数据？

**结论：RFB 协议是服务端先发，客户端后发；send_count=0 说明前端在收到首包前就被关闭或从未收到首包。**

#### RFB 握手顺序（设计文档 `PHASE_4_VNC_PROXY_DESIGN.md`）

```
Server → Client: ProtocolVersion "RFB 003.008\n"  (1)
Client → Server: ProtocolVersion "RFB 003.008\n"  (2)
Server → Client: Security Types [1, 2]
Client → Server: Security Type 1
...
```

客户端**只有在收到服务端首包（ProtocolVersion）后**才会调用 `transport.send()` 发送响应。

#### 数据流路径

```
VmControl/Xvnc → QUIC recv → bridge_channel_quic (quic_to_channel) → Tauri emit → 前端 listen → onmessage → RFB 处理 → transport.send() → vnc_stream_send → channel tx → bridge (channel_to_quic) rx
```

`send_count` 统计的是 `bridge_channel_quic` 中 `rx.recv()` 收到的次数，即 `vnc_stream_send` 写入 channel 的次数。**send_count=0 等价于：前端从未调用过 `VncBridgeTransport.send()`。**

#### 可能原因

| 原因 | 说明 |
|------|------|
| **A. 前端从未收到首包** | quic_to_channel 未从 VmControl 读到数据，或 emit 失败，或前端 listener 未就绪 |
| **B. 连接在首包到达前被关闭** | 7577c885 在收到 ProtocolVersion 前被 close，RFB 无机会发送 |
| **C. 首包到达但 RFB 已关闭** | 竞态：close 先于 onmessage 处理完成 |

结合「后端全链路成功」和「Disconnection timed out」，更可能是 **B**：连接在首包到达前被关闭，或首包到达过晚，导致 noVNC 超时断开。

---

### 2.2 为何会连续两次 vnc_stream_connect？

**结论：存在多种触发路径，可归纳为：重连/重试、或不同 streamKey 的订阅切换。**

#### 触发路径

| 路径 | 代码位置 | 说明 |
|------|----------|------|
| **reconnectVNCStream** | `vncStream.ts:336` | `disconnectStream` + `setTimeout(connectStream, 100)`，如 startVm 后调用 |
| **disconnect 重试** | `vncStream.ts:240-244` | status=error 时 `setTimeout(connectStream, delay)`，delay=2s×2^(retryCount-1) |
| **不同 streamKey 订阅** | `VNCViewShared` | streamKey=agentId 或 deviceId，切换设备/Agent 会 unsubscribe 旧 + subscribe 新 |

#### 时间线解读

- 11:26:19 第一次 connect(7577c885)
- 11:26:23 第二次 connect(89f7982b) —— 间隔约 4 秒

4 秒可能对应：

- 第一次重试：2s
- 第二次重试：2s + 4s = 6s（不符）
- 或：用户操作（如点击 Start）触发 `reconnectVNCStream`，在 11:26:23 执行

更合理的解释：**第一次连接失败或超时后，由重试或 `reconnectVNCStream` 触发第二次 connect。**

---

### 2.3 为何 7577c885 在 89f7982b 建立后约 10ms 就被 close？

**结论：新连接建立后，旧连接对应的组件或逻辑执行了 disconnect/close，形成「先建新、后关旧」的时序。**

#### 场景一：reconnectVNCStream

```javascript
// vncStream.ts:336
disconnectStream(streamKey);           // 先 close 7577c885
setTimeout(() => connectStream(...), 100);  // 100ms 后 connect 89f7982b
```

按此逻辑应是 **先 close 再 connect**，与「connect 89f7982b 后 10ms close 7577c885」不符。

#### 场景二：不同 streamKey 的订阅切换（更符合现象）

```
1. 订阅 streamKey=A（如 deviceId_A）→ connect 7577c885
2. 用户切换设备/视图，订阅 streamKey=B（如 deviceId_B）→ connect 89f7982b
3. 旧组件 unmount，unsubscribe(streamKey=A) → disconnectStream(A) → close 7577c885
```

React 的 effect 执行顺序可能是：新组件 mount → subscribe(B) → connect 89f7982b；随后旧组件 unmount → cleanup → unsubscribe(A) → close 7577c885。两者间隔约 10ms 是合理的。

#### 场景三：disconnect 事件与重试的竞态

```
1. 7577c885 的 RFB 触发 disconnect（如 "Disconnection timed out"）
2. disconnect 中：close(7577c885)、state.transportOrUrl=null、调度 retry
3. 若同时有 reconnectVNCStream 或快速 retry，可能先建立 89f7982b，再在 cleanup 中 close 7577c885
```

综合来看，**场景二（不同 streamKey 的订阅切换）** 最能解释「新连接建立后约 10ms 关闭旧连接」的时序。

---

### 2.4 可能根因与因果链

#### 根因猜测

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根因：首包到达前连接被关闭，或首包从未到达                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
┌───────────────┐        ┌─────────────────┐        ┌─────────────────────┐
│ VmControl/Xvnc │        │ 前端过早 close   │        │ 订阅/视图切换竞态    │
│ 首包延迟      │        │ (超时/用户操作)   │        │ 导致旧连接被替换      │
└───────────────┘        └─────────────────┘        └─────────────────────┘
```

#### 因果链（最可能）

1. **11:26:19**：第一次 connect(7577c885)，RFB 创建，等待服务端 ProtocolVersion。
2. **11:26:19–23**：QUIC/VmControl/Xvnc 建连或首包有延迟，前端在 4 秒内未收到首包。
3. **11:26:23**：发生其一或组合：
   - 用户切换设备/视图 → 新 streamKey 订阅 → connect 89f7982b；
   - 或 noVNC 超时（如 3s disconnect timeout）→ disconnect；
   - 或用户点击 Start → reconnectVNCStream。
4. **11:26:23**：旧连接 7577c885 被 close（unsubscribe 或 disconnect 中关闭）。
5. **send_count=0**：7577c885 从未收到首包，RFB 从未调用 `send()`。
6. **"Disconnection timed out"**：VncBridgeTransport 的 close 未实现 WebSocket 关闭握手，noVNC 等待 3s 后超时。

---

## 三、修复建议

### 3.1 高优先级

| 建议 | 说明 | 涉及文件 |
|------|------|----------|
| **延长首包等待** | 在 RFB/transport 层增加「首包超时」配置，避免在 VmControl 建连慢时过早断开 | `vncStream.ts`、`vncBridge.ts`、config |
| **VncBridgeTransport 关闭握手** | 参考 `vnc_bridge.rs`，在 close 时发送语义化 close 事件，减少 noVNC "Disconnection timed out" | `vncBridge.ts`、后端 emit close |
| **订阅切换时复用连接** | 相同 resourceId 的 streamKey 切换时，优先复用已有连接，避免频繁建连/关连 | `vncStream.ts`、`subscribeToVNCStream` |

### 3.2 中优先级

| 建议 | 说明 | 涉及文件 |
|------|------|----------|
| **reconnectVNCStream 防抖** | 在 connecting 状态下避免立即 disconnect+connect，可等待当前连接完成或超时 | `vncStream.ts` |
| **首包到达日志** | 在 quic_to_channel 首包、前端 onmessage 首包处打日志，便于确认首包是否到达 | `vnc_proxy.rs`、`vncBridge.ts` |
| **ensure_vnc_endpoint 错误透传** | 将 VmControl/Xvnc 错误通过 close reason 传到前端，便于区分「无首包」与「建连失败」 | `tunnel.rs`、`vnc_proxy.rs` |

### 3.3 低优先级

| 建议 | 说明 |
|------|------|
| **streamKey 规范化** | 统一 agentId/deviceId 作为 streamKey 的规则，减少重复订阅 |
| **连接复用策略** | 多组件共享同一 streamKey 时，避免重复 connect，已有逻辑可加强校验 |

---

## 四、验证建议

1. **复现**：在 VmControl 侧人为延迟首包（如 sleep 5s），观察是否出现 send_count=0 与 "Disconnection timed out"。
2. **日志**：在 `quic_to_channel` 首次 `recv_count`、前端 `[1-Bridge] 收到 data #1` 处加日志，确认首包是否到达前端。
3. **时序**：记录 subscribe/unsubscribe、connect、close 的精确时间戳，验证「新连接建立后 10ms 关闭旧连接」是否来自订阅切换。

---

## 五、相关代码索引

| 功能 | 文件 |
|------|------|
| channel→quic send_count | `vnc_proxy.rs:570-582` |
| vnc_stream_connect | `vnc_stream.rs:91-150` |
| VncBridgeTransport | `vncBridge.ts` |
| connectStream / reconnectVNCStream | `vncStream.ts:128-339` |
| subscribeToVNCStream | `vncStream.ts:319-347` |
| RFB 握手 | `novnc-core/rfb.js`、`PHASE_4_VNC_PROXY_DESIGN.md` |
| Disconnection timed out | noVNC `DISCONNECT_TIMEOUT=3`，`VNC_GAPS_ROUND3.md` |
