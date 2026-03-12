# VNC 统一 Bridge 方案 B 设计

> **与方案 A 不同思路**：方案 A 延续「非 OTA 直连 WebSocket、OTA 用 Bridge 兜底」的双轨制；方案 B 采用 **IPC 统一模式**，彻底消除 WebSocket 服务器，VncProxy 仅作为 Tauri 内部服务提供 bridge 能力。

---

## 一、背景与目标

### 1.1 当前架构

| 模式 | 数据流 | 问题 |
|------|--------|------|
| **非 OTA** | 浏览器 `ws://127.0.0.1:port/vnc/...` → VncProxy (HTTP+WS) → QUIC → Tunnel → QEMU/Xvnc | 依赖中间 WebSocket 服务器 |
| **OTA** | noVNC ←IPC→ `vnc_bridge_connect` ←Tauri 连 ws→ VncProxy → 同上 | Mixed Content 规避，双轨实现 |

### 1.2 方案 B 目标

1. **统一数据流**：无论 OTA 与否，前端一律通过 Tauri IPC 获取 VNC 流
2. **消除中间 WebSocket**：VncProxy 不再对外暴露 HTTP/WebSocket 服务
3. **差异最小化**：OTA 与非 OTA 仅剩「页面来源」差异，连接逻辑完全一致

---

## 二、架构图

### 2.1 统一后整体架构

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              前端 (novaic-app)                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  AgentDesktopView / DeviceDesktopView / VNCViewShared / vncStream                        │
│       │                                                                                 │
│       └─ createVncTransport(target)  → 一律使用 VncBridgeTransport                     │
│               │                                                                         │
│               └─ invoke('vnc_stream_connect', { resourceId, pcClientId })                │
│                       │                                                                 │
│                       └─ RFB(container, transport)  ← transport 为 IPC Bridge 实现         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ Tauri IPC（invoke + emit）
                                        │ 不再有 ws:// 直连分支
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          Tauri 内部：VncStreamService（原 VncProxy 逻辑）                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  • 无 HTTP 服务器、无 WebSocket 监听                                                     │
│  • vnc_stream_connect(resourceId, pcClientId) → 返回 stream_id                          │
│  • 内部：route_vnc 逻辑（本机 vs 远端）→ QUIC → tunnel                                   │
│  • 双向流：emit('vnc_stream:{id}:data', base64) / vnc_stream_send(id, data)              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                    │                                    │
                    │ 本机 QUIC loopback                  │ 远端 P2P relay
                    ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  p2p::tunnel::open_vnc_stream(conn, resource_id)                                        │
│  • 开 QUIC stream，写入头部 [0x01][len][resource_id]                                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ QUIC stream
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  PC 侧 tunnel server (p2p/tunnel.rs)                                                      │
│  • handle_incoming_stream → ensure_vnc_endpoint → proxy_quic_to_unix                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ Unix socket (RFB)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  QEMU / Xvnc                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 方案 B vs 方案 A 对比

| 维度 | 方案 A（双轨） | 方案 B（IPC 统一） |
|------|----------------|--------------------|
| 非 OTA 传输 | 浏览器直连 ws:// | 一律通过 IPC Bridge |
| OTA 传输 | IPC Bridge | 同上 |
| VncProxy 形态 | HTTP 服务器 + WebSocket | 无 HTTP Server，仅内部服务 |
| 前端分支 | `shouldUseVncBridge()` 二选一 | 无分支，统一 `VncBridgeTransport` |
| 端口占用 | 127.0.0.1:{动态} | 无 |

---

## 三、数据流详解

### 3.1 端到端数据流（统一后）

```
noVNC
  │
  │ send(data) / onmessage
  ▼
VncBridgeTransport (前端)
  │ invoke('vnc_stream_send', { streamId, data })
  │ listen('vnc_stream:{id}:data', base64 → onmessage)
  ▼
Tauri VncStreamService
  │ 内部：QUIC SendStream / RecvStream
  ▼
p2p::tunnel::open_vnc_stream
  │ QUIC stream
  ▼
PC Tunnel Server → proxy_quic_to_unix
  │ Unix socket
  ▼
QEMU / Xvnc (RFB)
```

### 3.2 非 OTA 与 OTA 的差异（方案 B 下）

| 项目 | 非 OTA | OTA | 说明 |
|------|--------|-----|------|
| 页面来源 | tauri://localhost / file:// | https://relay.gradievo.com | 仅此差异 |
| 连接入口 | `createVncTransport(target)` | 同上 | 完全一致 |
| 传输实现 | VncBridgeTransport | 同上 | 完全一致 |
| Tauri 命令 | vnc_stream_connect | 同上 | 完全一致 |
| 后端路由 | route_vnc → local/remote | 同上 | 完全一致 |

**结论**：方案 B 下，OTA 与非 OTA 的差异仅剩「页面加载来源」，所有 VNC 连接逻辑完全统一。

---

## 四、改动清单

### 4.1 删除 / 废弃

| 模块 | 改动 |
|------|------|
| `vnc_proxy.rs` | 删除 HTTP 服务器、WebSocket 监听、`/vnc/:device_id/:agent_id` 路由 |
| `VncProxyServer` | 删除 `TcpListener`、`axum::serve`、`port` 字段 |
| `get_vnc_proxy_url` | 废弃，前端不再请求 WebSocket URL |
| `shouldUseVncBridge()` | 删除，前端不再分支 |
| `vncBridge.ts` 中的 OTA 判断 | 保留 `VncBridgeTransport` 实现，但改名为通用 `VncStreamTransport` |

### 4.2 新增 / 重构

| 模块 | 改动 |
|------|------|
| **VncStreamService**（新） | 抽取 `vnc_proxy.rs` 中的 `route_vnc`、`serve_local_vnc`、`serve_remote_vnc`、`bridge_ws_quic` 逻辑，改为「流式接口」：接收 `(resource_id, pc_client_id)`，返回 `stream_id`，通过 channel/emit 双向传输 |
| **vnc_stream_connect**（新命令） | 替代 `vnc_bridge_connect`，内部直接调用 VncStreamService，不再连接 ws:// |
| **vnc_stream_send** | 与现有 `vnc_bridge_send` 语义相同，仅重命名 |
| **vnc_stream_close** | 与现有 `vnc_bridge_close` 语义相同，仅重命名 |
| **VncStreamTransport**（前端） | 原 `VncBridgeTransport` 重命名，`connect()` 调用 `vnc_stream_connect` |
| **createVncTransport** | 移除 `shouldUseVncBridge()` 分支，一律返回 `VncStreamTransport` |

### 4.3 保留不变

| 模块 | 说明 |
|------|------|
| `p2p/tunnel.rs` | open_vnc_stream、handle_incoming_stream、proxy_quic_to_unix 不变 |
| `p2p/vnc_endpoint.rs` | ensure_vnc_endpoint 不变 |
| `p2p/client.rs` | connect、connect_direct 不变 |
| `vnc_urls.rs` 中的 resolve 逻辑 | 可迁移到 vnc_stream_connect 内部，用于 pc_client_id 解析 |
| noVNC / RFB | 接口不变，仍接收 WebSocket 兼容的 transport |

### 4.4 文件级改动汇总

| 文件 | 操作 |
|------|------|
| `novaic-app/src-tauri/src/vnc_proxy.rs` | 重构为 `vnc_stream_service.rs`，移除 HTTP/WS，保留 route + QUIC bridge 逻辑 |
| `novaic-app/src-tauri/src/commands/vnc_bridge.rs` | 重构为 `vnc_stream.rs`，`vnc_stream_connect` 直接调用 service，不再连 ws |
| `novaic-app/src-tauri/src/commands/vnc_urls.rs` | 废弃 `get_vnc_proxy_url`，或保留仅作兼容（返回错误提示迁移） |
| `novaic-app/src/services/vncBridge.ts` | 重命名为 `vncStreamTransport.ts`，移除 `shouldUseVncBridge`，`connect` 调用 `vnc_stream_connect` |
| `novaic-app/src/services/vncTransport.ts` | 移除分支，一律 `new VncStreamTransport(...).connect()` |
| `novaic-app/src/services/vm.ts` | 移除 `shouldUseVncBridge` 相关逻辑 |
| `novaic-app/src-tauri/src/setup.rs` | 移除 VncProxyServer 启动，注册 VncStreamService |
| `novaic-app/src-tauri/src/lib.rs` | 命令改为 vnc_stream_connect/send/close |

---

## 五、优缺点评估

### 5.1 优点

| 优点 | 说明 |
|------|------|
| **统一性** | OTA 与非 OTA 完全一致，无分支，代码路径单一 |
| **无 Mixed Content** | 不再有 ws://，从根本上消除问题 |
| **无端口占用** | 不再监听 127.0.0.1，减少端口冲突和防火墙顾虑 |
| **简化部署** | 移动端无需考虑「VncProxy 端口是否可达」 |
| **可维护性** | 删除 `shouldUseVncBridge`、双轨传输，降低心智负担 |

### 5.2 缺点

| 缺点 | 说明 |
|------|------|
| **非 OTA 多一层 IPC** | 原可浏览器直连 ws，现需经 Tauri IPC，有序列化/事件开销 |
| **性能** | base64 编码/解码、IPC 序列化，理论上略逊于裸 WebSocket（实际影响需压测） |
| **调试** | 无法用浏览器开发者工具直接抓 ws 帧，需通过 Tauri 日志 |

### 5.3 风险

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| IPC 性能不足 | 中 | 压测 VNC 帧率；必要时可探索 binary IPC 或 SharedArrayBuffer |
| 迁移期兼容 | 低 | 保留 `get_vnc_proxy_url` 一段时间，返回明确错误引导迁移 |
| 共享流（vncStream） | 中 | 共享流当前可能复用同一 ws；改为复用同一 stream_id，需验证逻辑 |

---

## 六、迁移步骤

### Phase 1：后端 VncStreamService（约 1 周）

1. 新建 `vnc_stream_service.rs`，从 `vnc_proxy.rs` 抽取：
   - `route_vnc`、`serve_local_vnc`、`serve_remote_vnc`
   - `bridge_ws_quic` 改为 `bridge_channel_quic`：用 `mpsc::channel` 替代 WebSocket
2. 实现 `connect_stream(resource_id, pc_client_id) -> stream_id`，内部 spawn 任务做 QUIC 双向转发，通过 channel 与 emit 与前端通信
3. 新建 `vnc_stream.rs` 命令：`vnc_stream_connect`、`vnc_stream_send`、`vnc_stream_close`
4. 注册命令，**保留** 原有 `vnc_bridge_*` 和 VncProxyServer，双轨运行

### Phase 2：前端统一入口（约 0.5 周）

1. 将 `VncBridgeTransport` 重命名为 `VncStreamTransport`
2. `connect()` 改为调用 `vnc_stream_connect`（不再调用 `vnc_bridge_connect`）
3. 事件名改为 `vnc_stream:{id}:data`、`vnc_stream:{id}:close`
4. `createVncTransport` 移除 `shouldUseVncBridge()` 分支，一律使用 `VncStreamTransport`
5. 删除 `shouldUseVncBridge` 导出及所有引用

### Phase 3：下线旧路径（约 0.5 周）

1. 停止启动 VncProxyServer（`setup.rs` 中注释或移除）
2. 废弃 `get_vnc_proxy_url`，调用时返回错误或重定向到新说明
3. 删除 `vnc_bridge_connect/send/close` 及 `VncBridgeState`
4. 删除 `vnc_proxy.rs` 中的 HTTP/WebSocket 相关代码，或整文件替换为精简版

### Phase 4：验证与收尾（约 0.5 周）

1. 非 OTA 场景：桌面 App 启动，连接本机/远端 VNC，验证画质与延迟
2. OTA 场景：HTTPS 页面连接，验证无 Mixed Content、连接正常
3. 共享流（vncStream）：多组件共享同一 VNC 目标，验证复用与断开
4. 清理未使用代码、更新文档

---

## 七、附录：VncStreamService 伪代码

```rust
// vnc_stream_service.rs 核心逻辑（伪代码）

pub async fn connect_stream(
    resource_id: &str,
    pc_client_id: Option<&str>,
    app: AppHandle,
) -> Result<String, String> {
    let device_id = resolve_pc_client_id(pc_client_id).await?;
    let stream_id = uuid::Uuid::new_v4().to_string();
    let (tx, mut rx) = mpsc::channel::<Vec<u8>>(64);
    REGISTRY.insert(stream_id.clone(), tx);

    let (quic_send, quic_recv) = if local_vmcontrol.device_id == device_id {
        let conn = get_or_create_local_conn().await?;
        p2p::tunnel::open_vnc_stream(&conn, resource_id).await?
    } else {
        let conn = get_or_create_remote_conn(device_id).await?;
        p2p::tunnel::open_vnc_stream(&conn, resource_id).await?
    };

    let data_event = format!("vnc_stream:{}:data", stream_id);
    let close_event = format!("vnc_stream:{}:close", stream_id);

    tauri::async_runtime::spawn(async move {
        // 双向桥接：rx ↔ quic_send, quic_recv → emit(data_event)
        bridge_channel_quic(rx, quic_send, quic_recv, &app, &data_event, &close_event).await;
        REGISTRY.remove(&stream_id);
    });

    Ok(stream_id)
}
```

---

*文档版本：2026-03，基于 novaic-app 代码库*
