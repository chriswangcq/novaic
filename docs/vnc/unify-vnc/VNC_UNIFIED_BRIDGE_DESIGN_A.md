# VNC 统一 Bridge 方案 A

> **目标**：无论是否 OTA，都走统一模式；不再依赖中间 WebSocket，VncProxy 直接提供 bridge 能力。

---

## 一、现状与问题

### 1.1 当前架构

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  非 OTA（file://、tauri://、本地开发）                                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  noVNC  ──ws://127.0.0.1:port/vnc/...──►  VncProxy (axum WS)  ──►  route_vnc  ──►  QUIC │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  OTA（HTTPS 页面，Mixed Content 禁止 ws://）                                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  noVNC  ──IPC──►  vnc_bridge_connect  ──tokio_tungstenite──►  ws://127.0.0.1:port/vnc/  │
│                        │                                        │                        │
│                        │  Tauri 连接自己的 VncProxy WebSocket    │                        │
│                        └────────────────────────────────────────┴──►  VncProxy  ──►  QUIC │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 问题

| 问题 | 说明 |
|------|------|
| **中间 WebSocket** | OTA 时 Tauri 通过 `connect_async(ws_url)` 连接本机 VncProxy，形成「进程内 TCP 环回」，多余一跳 |
| **双路径维护** | `createVncTransport` 分支：`shouldUseVncBridge()` → VncBridgeTransport，否则 get_vnc_proxy_url |
| **逻辑重复** | vnc_bridge 与 vnc_proxy 的 device_id 解析、路由决策逻辑重复（resolve_device_id 与 get_vnc_proxy_url 各自实现） |

---

## 二、方案 A 架构设计

### 2.1 核心思路

**VncProxy 直接提供 Bridge 能力**：将「建立 QUIC 流并桥接数据」的逻辑抽象为可接受多种「双向流」的实现。OTA 时，Bridge 直接调用该逻辑，传入 IPC channel 作为流，**不再经过 WebSocket**。

### 2.2 统一后架构图

```
                              ┌──────────────────────────────────────────────────────────────┐
                              │                    前端 (noVNC + createVncTransport)          │
                              └──────────────────────────────────────────────────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
            ┌───────────────┐               ┌───────────────┐               ┌───────────────┐
            │  非 OTA       │               │  OTA          │               │  统一后端     │
            │  ws:// 直连   │               │  IPC Bridge   │               │  VncProxy     │
            └───────┬───────┘               └───────┬───────┘               └───────┬───────┘
                    │                               │                               │
                    │  WebSocket                    │  invoke/emit                   │
                    │  (浏览器可连)                  │  (Mixed Content 安全)         │
                    │                               │                               │
                    └───────────────────────────────┼───────────────────────────────┘
                                                    │
                                                    ▼
                              ┌──────────────────────────────────────────────────────────────┐
                              │  VncProxy 统一入口：route_vnc_core(stream)                    │
                              │  • stream 实现：WebSocketStream | BridgeChannelStream         │
                              │  • 共用：resolve_device_id、serve_local_vnc、serve_remote_vnc   │
                              └──────────────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
                              ┌──────────────────────────────────────────────────────────────┐
                              │  QUIC stream  ←→  Tunnel Server  ←→  QEMU/Xvnc               │
                              └──────────────────────────────────────────────────────────────┘
```

### 2.3 数据流对比

| 阶段 | 非 OTA（改造后） | OTA（改造后） |
|------|------------------|----------------|
| 1. 传输建立 | `get_vnc_proxy_url` → ws:// | `vnc_bridge_connect` → bridge_id |
| 2. 数据入口 | 浏览器 WebSocket → vnc_handler | IPC (vnc_bridge_send / emit) → bridge task |
| 3. 统一核心 | **route_vnc_core(ws_stream)** | **route_vnc_core(bridge_stream)** |
| 4. 后端 | serve_local/remote_vnc → QUIC | 同上 |
| 5. 终点 | QEMU/Xvnc | 同上 |

**差异点**：仅第 1、2 步的「传输层建立方式」不同，第 3–5 步完全一致。

---

## 三、数据流详图

### 3.1 端到端数据流（统一后）

```
┌─────────┐     ┌─────────────────────────────────────────────────────────────────────────┐
│  noVNC  │     │  VncProxy 统一核心                                                       │
│  RFB    │     │                                                                         │
└────┬────┘     │  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐   │
     │          │  │ IncomingStream   │    │ route_vnc_core    │    │ QUIC ↔ Unix     │   │
     │ 非OTA    │  │ (trait/impl)     │───►│ • resolve device  │───►│ proxy_quic_to_  │   │
     │ ws://    │  │ • WebSocket      │    │ • local/remote    │    │ unix            │   │
     │          │  │ • BridgeChannel  │    │ • open_vnc_stream │    └────────┬────────┘   │
     │ OTA      │  └─────────────────┘    └──────────────────┘             │            │
     │ IPC      │         ▲                                                    │            │
     └──────────┼─────────┘                                                    │            │
                │                                                              ▼            │
                │  bridge: mpsc ◄──► emit/listen                              QEMU/Xvnc   │
                └─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 从 noVNC 到 QEMU/Xvnc 的完整路径

```text
[非 OTA]
noVNC.attach(ws_url)
  → WebSocket 连接 ws://127.0.0.1:{port}/vnc/{device_id}/{resource_id}
  → vnc_handler → route_vnc_core(WebSocketStream)
  → serve_local_vnc / serve_remote_vnc
  → open_vnc_stream(conn, agent_id)
  → bridge_ws_quic(ws, quic_send, quic_recv)
  → PC tunnel server → proxy_quic_to_unix
  → ensure_vnc_endpoint(resource_id) → Unix socket
  → QEMU -vnc unix:... / Xvnc

[OTA]
noVNC.attach(VncBridgeTransport)
  → VncBridgeTransport.connect() → invoke('vnc_bridge_connect', { resourceId, pcClientId })
  → vnc_bridge_connect 内部调用 route_vnc_core(BridgeChannelStream)
  → （后续与上同）serve_local/remote → open_vnc_stream → bridge
  → BridgeChannelStream: mpsc ◄──► emit vnc_bridge:{id}:data
  → 前端 listen → onmessage → noVNC
```

---

## 四、改动清单

### 4.1 模块改动总览

| 模块 | 文件 | 改动类型 | 说明 |
|------|------|----------|------|
| **vnc_proxy** | `vnc_proxy.rs` | 重构 | 抽象 `VncStream` trait，抽 `route_vnc_core` |
| **vnc_bridge** | `vnc_bridge.rs` | 重构 | 移除 `connect_async(ws_url)`，调用 `route_vnc_core` |
| **vnc_urls** | `vnc_urls.rs` | 保留 | `resolve_device_id` 抽到共享模块，供 bridge 复用 |
| **前端** | `vncTransport.ts` | 微调 | 逻辑不变，可选：统一走 bridge 时移除 get_vnc_proxy_url 分支 |
| **前端** | `vncBridge.ts` | 不变 | 接口不变，仍为 VncBridgeTransport |

### 4.2 详细改动

#### 4.2.1 vnc_proxy.rs

```rust
// 新增：双向流抽象
pub trait VncStream: Send + 'static {
    fn split(self) -> (impl Sink<Vec<u8>> + Send, impl Stream<Item = Vec<u8>> + Send);
}

// WebSocket 实现
impl VncStream for WebSocket { ... }

// 核心逻辑抽取
pub async fn route_vnc_core<S: VncStream>(
    stream: S,
    device_id: &str,
    agent_id: &str,
    state: HandlerState,
) -> anyhow::Result<()> {
    // 原 route_vnc 的 local/remote 判断 + serve_local_vnc / serve_remote_vnc
    // 将 bridge_ws_quic 泛化为 bridge_stream_quic(stream, quic_send, quic_recv)
}

// vnc_handler 改为
async fn vnc_handler(...) {
    route_vnc_core(ws_socket, &device_id, &agent_id, state).await
}
```

#### 4.2.2 vnc_bridge.rs

```rust
// 移除
// let (ws_stream, _) = tokio_tungstenite::connect_async(&ws_url).await?;

// 改为
let (tx, rx) = mpsc::channel::<Vec<u8>>(64);
let (quic_to_frontend_tx, quic_to_frontend_rx) = ...;  // 或复用 tx 方向

// 构造 BridgeChannelStream，实现 VncStream
let bridge_stream = BridgeChannelStream::new(tx, quic_to_frontend_rx);

// 直接调用 route_vnc_core（需要传入 proxy state、resolve device_id）
let device_id = resolve_device_id(...).await?;
tauri::async_runtime::spawn(async move {
    let state = ...;  // 从 VncProxyState 获取 HandlerState
    if let Err(e) = route_vnc_core(bridge_stream, &device_id, &resource_id, state).await {
        app.emit(&close_event, &e.to_string());
    }
});
```

#### 4.2.3 共享 resolve_device_id

- 从 `vnc_bridge.rs` 和 `vnc_urls.rs` 中抽到 `vnc_proxy.rs` 或新建 `vnc_common.rs`
- `get_vnc_proxy_url` 和 `vnc_bridge_connect` 都调用同一实现

### 4.3 可选：统一走 Bridge

若希望「非 OTA 与 OTA 差异点尽量小」，可进一步：

- `createVncTransport` **始终**返回 `VncBridgeTransport`
- 移除 `get_vnc_proxy_url` 的调用分支
- 非 OTA 时浏览器也可用 IPC（Tauri 环境下 `invoke` 可用），无 Mixed Content 问题

此时 VncProxy 的 `/vnc` WebSocket 路由可保留用于：
- 调试、curl/websocat 手动测试
- 未来可能的非 Tauri 客户端（如独立 Web 应用 + 本地代理）

---

## 五、迁移路径

### 5.1 阶段 1：后端抽象（1–2 天）

1. 在 `vnc_proxy.rs` 中定义 `VncStream` trait 或等效抽象
2. 将 `route_vnc` 逻辑抽成 `route_vnc_core<S: VncStream>(stream, device_id, agent_id, state)`
3. `vnc_handler` 调用 `route_vnc_core(ws, ...)`
4. 验证非 OTA 行为不变

### 5.2 阶段 2：Bridge 直连（1 天）

1. 实现 `BridgeChannelStream`，包装 `mpsc::Sender` + 接收端
2. `vnc_bridge_connect` 改为调用 `route_vnc_core(bridge_stream, ...)`，移除 `connect_async`
3. 抽 `resolve_device_id` 到共享模块，bridge 与 vnc_urls 复用
4. 验证 OTA 模式行为不变

### 5.3 阶段 3：前端收敛（可选，0.5 天）

1. 若采用「统一走 Bridge」：`createVncTransport` 移除 `shouldUseVncBridge` 分支，始终 `new VncBridgeTransport`
2. 移除或标记废弃 `get_vnc_proxy_url` 在 VNC 场景的调用
3. 回归测试：非 OTA、OTA、本机、远端、maindesk、subuser

### 5.4 依赖关系

```
阶段 1 (vnc_proxy 抽象)
    │
    └──► 阶段 2 (vnc_bridge 直连)
              │
              └──► 阶段 3 (前端统一，可选)
```

---

## 六、优缺点评估

### 6.1 优点

| 项目 | 说明 |
|------|------|
| **消除中间 WebSocket** | OTA 时不再有 Tauri → ws://127.0.0.1 → VncProxy 的冗余连接 |
| **逻辑统一** | route_vnc_core 单一实现，WebSocket 与 Bridge 共用，减少重复与漂移 |
| **差异最小化** | 非 OTA 与 OTA 仅「传输建立方式」不同，核心路径完全一致 |
| **可测试性** | 可注入 MockStream 做单元测试 |
| **扩展性** | 未来新增传输类型（如 WebTransport）只需实现 VncStream |

### 6.2 缺点与缓解

| 项目 | 说明 | 缓解 |
|------|------|------|
| **抽象复杂度** | 引入 trait/泛型，代码略复杂 | 保持 trait 简单，仅 split + 双向流语义 |
| **状态传递** | bridge 需访问 HandlerState（local_conn、remote_conns 等） | 通过 `tauri::State` 注入，与现有一致 |
| **错误传播** | bridge 在 spawn 的 task 内，错误需通过 emit 传到前端 | 已有 close_event 机制，沿用即可 |

### 6.3 风险

| 风险 | 等级 | 应对 |
|------|------|------|
| 重构引入回归 | 中 | 阶段 1 后充分验证非 OTA；阶段 2 后验证 OTA |
| HandlerState 跨 task 传递 | 低 | HandlerState 为 Arc 包装，clone 后传入 spawn 即可 |
| 超时与 Close reason | 低 | route_vnc_core 内已有超时逻辑，bridge 需在 stream 侧实现超时或复用 |

---

## 七、与现有方案的关系

- **P2P 竞态修复**（R1–R5、E2）：与本方案正交，可并行
- **VNC 统一入口**（expert-advance）：本方案聚焦「传输层统一」，不涉及 maindesk/subuser 后端统一、VncTarget 等，可后续叠加
- **Scrcpy**：本方案仅针对 VNC；Scrcpy 仍走 WebSocket，如需可后续做类似 Bridge 抽象

---

## 八、总结

| 维度 | 方案 A |
|------|--------|
| **统一程度** | 高：核心逻辑单一，仅传输入口不同 |
| **改动量** | 中：vnc_proxy 重构 + vnc_bridge 改造，前端可选 |
| **迁移风险** | 低：分阶段、可回退 |
| **推荐** | 适合作为「VNC 统一 Bridge」的首选实现 |

---

*文档版本：R1 | 创建时间：2026-03-12*
