# VNC 统一 Bridge 方案 C：VncProxy 内嵌化 + 流式 IPC

**文档版本**: R1  
**创建时间**: 2026-03-12  
**目标**: 无论 OTA 与否，统一数据流；消除对中间 WebSocket 的依赖，VncProxy 直接提供 bridge 能力。

---

## 一、背景与问题

### 1.1 当前架构

| 模式 | 数据流 | 差异点 |
|------|--------|--------|
| **非 OTA** | noVNC → `ws://127.0.0.1:port/vnc/...` → VncProxy → QUIC → QEMU/Xvnc | 浏览器直连 WebSocket |
| **OTA** | noVNC → IPC → Tauri → `ws://127.0.0.1:port/vnc/...` → VncProxy → QUIC → QEMU/Xvnc | 因 Mixed Content，Tauri 代连 ws，再 IPC 桥接前端 |

### 1.2 核心矛盾

- **中间 WebSocket**：VncProxy 以 HTTP/WS 服务形式存在，OTA 时 Tauri 必须「连接 ws://」才能接入，形成「前端↔IPC↔Tauri↔WS↔VncProxy」的冗余链路
- **双轨实现**：前端需 `shouldUseVncBridge()` 分支，非 OTA 用 URL，OTA 用 VncBridgeTransport，逻辑分散

### 1.3 方案 C 核心思路

**VncProxy 不再作为独立 WebSocket 服务**，而是作为 Tauri 进程内的**流式模块**，直接暴露 `(SendStream, RecvStream)` 给调用方。前端**无论 OTA 与否**，统一通过 IPC 与 Tauri 通信，Tauri 内部直接调用 VncProxy 逻辑，**不再经过 ws://127.0.0.1**。

---

## 二、架构图

### 2.1 统一后整体架构

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              前端 (novaic-app)                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  AgentDesktopView / DeviceDesktopView / VNCViewShared / vncStream                       │
│       │                                                                                 │
│       └─ createVncTransport(target)  ← 统一入口，不再区分 OTA/非 OTA                    │
│              │                                                                          │
│              └─ invoke('vnc_stream_connect', { resourceId, pcClientId })                 │
│                     │                                                                   │
│                     └─ 返回 streamId，后续：                                             │
│                        • invoke('vnc_stream_send', { streamId, data })                   │
│                        • listen('vnc_stream:{streamId}:data', ...)                      │
│                        • listen('vnc_stream:{streamId}:close', ...)                     │
│                                                                                         │
│       └─ RFB(container, VncStreamTransport)  ← 统一使用同一 Transport 类型               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ IPC (invoke / emit)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          Tauri 进程内                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  vnc_stream 命令模块                                                                     │
│  • vnc_stream_connect(resourceId, pcClientId) → streamId                                │
│  • vnc_stream_send(streamId, data)                                                       │
│  • vnc_stream_close(streamId)                                                           │
│       │                                                                                 │
│       └─ 直接调用 VncProxyCore（无 HTTP/WS 层）                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  VncProxyCore（内嵌模块，非 HTTP 服务）                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  • open_vnc_stream(pc_client_id, resource_id) -> Result<(SendStream, RecvStream)>       │
│  • 复用现有 route 逻辑：local → QUIC loopback；remote → P2P connect                    │
│  • 复用现有 tunnel::open_vnc_stream、bridge 逻辑                                        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                    │                                    │
                    │ 本机                              │ 远端
                    ▼                                    ▼
┌──────────────────────────────┐    ┌──────────────────────────────────────────────────────┐
│  serve_local_vnc_stream       │    │  serve_remote_vnc_stream                              │
│  • 127.0.0.1 QUIC loopback   │    │  • P2P connect → Relay → PC 远端 QUIC tunnel           │
└──────────────────────────────┘    └──────────────────────────────────────────────────────┘
                    │                                    │
                    └────────────────┬───────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  p2p::tunnel::open_vnc_stream(conn, resource_id)                                        │
│  • 开 QUIC stream，写入头部 [0x01][len][resource_id]                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  PC 侧 tunnel server → ensure_vnc_endpoint → QEMU/Xvnc                                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流对比

| 阶段 | 当前（非 OTA） | 当前（OTA） | 方案 C（统一） |
|------|----------------|-------------|----------------|
| 前端→Tauri | — | IPC | IPC |
| Tauri 内部 | — | 连 ws:// → VncProxy | 直接调用 VncProxyCore |
| VncProxy | HTTP Upgrade → WS | 同上 | 无 HTTP，直接流 |
| 后续 | QUIC → Tunnel → QEMU | 同上 | 同上 |

**方案 C 的差异**：去掉「VncProxy 作为 HTTP/WS 服务」这一层，Tauri 直接持有 QUIC stream，通过 IPC 与前端双向转发。

---

## 三、数据流详解

### 3.1 端到端数据流（方案 C）

```
noVNC (RFB)
    │
    │  binary/text frames
    ▼
VncStreamTransport (前端)
    │  send(data) → invoke('vnc_stream_send', { streamId, data })
    │  onmessage ← listen('vnc_stream:{id}:data', base64)
    ▼
Tauri vnc_stream 命令
    │  mpsc channel ↔ bridge task
    ▼
VncProxyCore::open_vnc_stream
    │  route_vnc → serve_local / serve_remote
    ▼
p2p::tunnel::open_vnc_stream
    │  QUIC stream 双向
    ▼
Tunnel Server → ensure_vnc_endpoint → Unix socket
    │
    ▼
QEMU / Xvnc (RFB)
```

### 3.2 非 OTA 与 OTA 的差异（方案 C 下）

| 维度 | 非 OTA | OTA | 方案 C |
|------|--------|-----|--------|
| 前端传输类型 | WebSocket URL | VncBridgeTransport | **VncStreamTransport**（唯一） |
| 连接建立 | `new WebSocket(url)` | `VncBridgeTransport.connect()` | `VncStreamTransport.connect()` |
| 数据通道 | 浏览器 → ws:// | 浏览器 → IPC → Tauri → ws:// | 浏览器 → IPC → Tauri |
| Tauri 内部 | — | 连 ws:// | **直接调用 VncProxyCore** |

**结论**：方案 C 下，非 OTA 与 OTA 的差异**仅剩前端运行环境**（localhost vs CDN），**数据流完全一致**，都走 IPC。

---

## 四、改动清单

### 4.1 新增模块

| 模块 | 路径 | 职责 |
|------|------|------|
| VncProxyCore | `vnc_proxy_core.rs` 或 `vnc_proxy.rs` 重构 | 从 `route_vnc` + `serve_local/remote_vnc` 抽取纯流逻辑，无 HTTP |
| vnc_stream 命令 | `commands/vnc_stream.rs` | `vnc_stream_connect`、`vnc_stream_send`、`vnc_stream_close` |
| VncStreamTransport | `vncStreamTransport.ts` | 实现 WebSocket 兼容接口，内部用 invoke/listen |
| VncStreamState | `VncStreamState` | 管理 streamId → bridge task 的映射 |

### 4.2 修改模块

| 模块 | 路径 | 改动 |
|------|------|------|
| vnc_proxy.rs | `src-tauri/src/vnc_proxy.rs` | 拆分为：VncProxyCore（流逻辑）+ 可选 VncProxyServer（HTTP，兼容期保留） |
| vnc_bridge.rs | `commands/vnc_bridge.rs` | **废弃**，逻辑合并进 vnc_stream |
| vnc_urls.rs | `commands/vnc_urls.rs` | `get_vnc_proxy_url` **废弃**（或仅用于 Scrcpy 等非 VNC 场景） |
| vncTransport.ts | `src/services/vncTransport.ts` | `createVncTransport` 统一返回 `VncStreamTransport`，移除 `shouldUseVncBridge` 分支 |
| vncBridge.ts | `src/services/vncBridge.ts` | **废弃**，由 vncStreamTransport 取代 |
| useVnc.ts | `src/hooks/useVnc.ts` | 仅处理 `VncStreamTransport`，移除 `VncBridgeTransport` 分支 |
| vncStream.ts | `src/services/vncStream.ts` | 共享流改为基于 VncStreamTransport |

### 4.3 删除/废弃

| 项 | 说明 |
|----|------|
| VncProxy HTTP 服务 | 可选：迁移期保留，仅非 OTA 且未升级前端时使用；长期移除 |
| VncBridgeTransport | 由 VncStreamTransport 取代 |
| vnc_bridge_connect/send/close | 由 vnc_stream_connect/send/close 取代 |
| get_vnc_proxy_url（VNC 用途） | 前端不再请求 WS URL |

---

## 五、优缺点

### 5.1 优点

| 点 | 说明 |
|----|------|
| **数据流统一** | 无论 OTA 与否，前端→Tauri→VncProxyCore→QUIC→QEMU 完全一致 |
| **消除中间 WS** | 不再有「Tauri 连 ws://127.0.0.1」的冗余环节，减少延迟与故障点 |
| **前端简化** | 单一 Transport 类型，无 `shouldUseVncBridge` 分支 |
| **安全** | 不暴露 127.0.0.1 端口给浏览器，减少攻击面 |
| **可扩展** | 未来 Scrcpy、其他协议可复用同一「流式 IPC」模式 |

### 5.2 缺点

| 点 | 说明 |
|----|------|
| **必须 Tauri** | 纯 Web 部署（无 Tauri）无法使用，需依赖 Tauri 作为前端运行时 |
| **IPC 开销** | 相比浏览器直连 ws://，多一层 IPC 序列化（base64 等），但通常可接受 |
| **迁移成本** | 需重构 vnc_proxy、废弃 vnc_bridge、前端全面切换 |

### 5.3 风险

| 风险 | 缓解 |
|------|------|
| 旧版前端/后端兼容 | 迁移期保留 VncProxy HTTP + vnc_bridge，通过 feature flag 或版本协商逐步切换 |
| IPC 消息体过大 | 使用 binary IPC（Tauri 2 支持）或分片，避免 base64 膨胀 |
| 多窗口共享流 | 需在 VncStreamState 内做 stream 复用（同 resourceId+pcClientId 共享） |

---

## 六、迁移步骤

### Phase 1：Tauri 侧 VncProxyCore + vnc_stream（约 1 周）

1. 从 `vnc_proxy.rs` 抽取 `route_vnc`、`serve_local_vnc`、`serve_remote_vnc` 的**流式版本**，形成 `VncProxyCore::open_vnc_stream(pc_client_id, resource_id) -> (SendStream, RecvStream)`
2. 新增 `commands/vnc_stream.rs`：`vnc_stream_connect`、`vnc_stream_send`、`vnc_stream_close`
3. 实现 `VncStreamState`，管理 streamId → bridge task
4. 单元测试：`open_vnc_stream` 本机/远端路径

### Phase 2：前端 VncStreamTransport（约 0.5 周）

1. 新增 `vncStreamTransport.ts`，实现 `VncStreamTransport` 类（与 `VncBridgeTransport` 接口一致）
2. `connect()` 调用 `vnc_stream_connect`，`send()` 调用 `vnc_stream_send`，`listen` 接收 data/close
3. 修改 `createVncTransport`：**始终**返回 `VncStreamTransport`（移除 `shouldUseVncBridge` 分支）
4. 修改 `useVnc`、`vncStream`：仅支持 `VncStreamTransport`

### Phase 3：切换与验证（约 0.5 周）

1. 功能开关：`USE_VNC_STREAM=true` 时走新路径，否则保留旧路径
2. OTA 与非 OTA 场景全量测试
3. 性能对比：延迟、CPU、内存

### Phase 4：清理（约 0.5 周）

1. 移除 `vnc_bridge.rs`、`VncBridgeTransport`、`get_vnc_proxy_url`（VNC 用途）
2. 可选：移除 VncProxy HTTP 服务，或保留仅用于 Scrcpy 等

---

## 七、与方案 A、B 的对比（概念）

> 注：若方案 A/B 有明确定义，可在此补充。以下为基于常见思路的假设对比。

| 维度 | 方案 A（假设：保留 WS，统一前端） | 方案 B（假设：Gateway 提供 wss） | 方案 C（本方案） |
|------|----------------------------------|----------------------------------|------------------|
| 传输层 | 非 OTA 直连 ws，OTA 用 bridge | 统一 wss://gateway/... 代理 | 统一 IPC，无 WS |
| 中间层 | VncProxy 仍为 WS 服务 | Gateway 做 WS 代理 | VncProxy 内嵌，无 HTTP |
| 前端差异 | 仍有 OTA/非 OTA 分支 | 可能无 | **无** |
| 部署依赖 | 本地 VncProxy | Gateway 需支持 wss | Tauri 必须 |

---

## 八、附录：接口草案

### 8.1 Tauri 命令

```rust
// vnc_stream_connect(resourceId, pcClientId?) -> streamId
#[tauri::command]
pub async fn vnc_stream_connect(
    resource_id: String,
    pc_client_id: Option<String>,
    // ... state
) -> Result<String, String>;

// vnc_stream_send(streamId, data: Vec<u8>)
#[tauri::command]
pub async fn vnc_stream_send(stream_id: String, data: Vec<u8>) -> Result<(), String>;

// vnc_stream_close(streamId)
#[tauri::command]
pub async fn vnc_stream_close(stream_id: String) -> Result<(), String>;
```

### 8.2 前端事件

- `vnc_stream:{streamId}:data` — payload: base64 编码的二进制数据
- `vnc_stream:{streamId}:close` — payload: 关闭原因字符串

### 8.3 VncStreamTransport 接口（与 VncBridgeTransport 兼容）

```typescript
class VncStreamTransport {
  readyState: 0 | 1 | 2 | 3;
  protocol: string;
  onopen: (() => void) | null;
  onmessage: ((e: { data: ArrayBuffer | string }) => void) | null;
  onerror: ((e: unknown) => void) | null;
  onclose: ((e: { code?: number; reason?: string }) => void) | null;

  async connect(): Promise<void>;
  send(data: ArrayBuffer | string): void;
  close(): void;
}
```

---

*方案 C 设计完成。实施时建议先完成 Phase 1 的 VncProxyCore 抽取，确保本机/远端路径均可通过流式 API 工作，再推进前端迁移。*
