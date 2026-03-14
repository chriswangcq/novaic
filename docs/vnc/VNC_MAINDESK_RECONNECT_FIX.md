# Maindesk 重连失败问题：根因与修复

> 现象：maindesk 只有在 vmcontrol/tauri 重启后才能第一次连上，后面一直连不上。

---

## 一、根因分析

### 1.1 时序竞态

```
用户关闭 maindesk（或切到 subuser）
    │
    ├─ 前端：transport.close() → _evictFromCache，不调用 vnc_stream_close
    │
    └─ 后端：旧 stream 仍注册，heartbeat 每 20s touch，永不 30s 空闲超时

用户再次打开 maindesk
    │
    ├─ vnc_stream_connect → evict_for_resource
    │   └─ drop(tx) 关闭 channel，旧 route 任务开始退出
    │
    ├─ 立即创建新 stream，spawn route_vnc_to_channel
    │   └─ open_vnc_stream → 新 QUIC stream
    │   └─ tunnel 侧 handle_incoming_stream → ensure_vnc_endpoint → UnixStream::connect
    │
    └─ 竞态：旧 proxy_quic_to_unix 尚未退出，仍持有 QEMU Unix 连接
             新连接尝试 UnixStream::connect → QEMU 拒绝（单客户端）或 connect 失败
```

### 1.2 关键点

- **QEMU VNC**：`-vnc unix:path` 单客户端，新连接需等旧连接完全关闭
- **旧连接关闭链**：`drop(tx)` → `rx.recv()` 返回 None → `quic_send.finish()` → 服务端 `quic_recv.read()` 返回 → `proxy_quic_to_unix` 退出 → Unix 连接关闭
- **竞态**：新连接在旧 proxy 退出前就发起 `UnixStream::connect`，导致失败

### 1.3 为何重启后第一次能连

重启后无旧连接，无 eviction，直接建连，无竞态。

---

## 二、修复方案

### 2.1 已实现：eviction 后延迟

在 `vnc_stream.rs` 中，`evict_for_resource` 返回是否驱逐了旧连接；若驱逐，则 sleep 250ms 再创建新 stream：

```rust
let had_old = stream_state.evict_for_resource(&resource_id, &app).await;
if had_old {
    tokio::time::sleep(Duration::from_millis(250)).await;
}
```

250ms 足够旧 proxy 退出并关闭 QEMU Unix 连接。

### 2.2 备选：前端显式 close

前端 `transport.close()` 时调用 `vnc_stream_close`，可立即关闭后端 stream，减少竞态窗口。当前实现依赖 30s 空闲或 eviction，未采用此方案。

---

## 三、验证

1. 启动 app，打开 maindesk，确认能连上
2. 关闭 maindesk（或切到 subuser 再切回）
3. 再次打开 maindesk，应能正常连接

若仍失败，可查日志：

- `[VNC-FLOW] [4-vnc_stream] 连接池 驱逐旧连接`：发生了 eviction
- `[VNC-FLOW] [6-Tunnel] Unix socket 连接成功`：Unix 连接成功
- `VNC Unix connect to ... failed`：Unix 连接失败（竞态或 socket 不存在）

---

*文档基于 2026-03 修复*
