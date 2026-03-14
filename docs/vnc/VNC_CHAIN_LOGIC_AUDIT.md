# VNC 复杂链路逻辑审计

> 从 DeviceDesktopView → createVncTransport → vncBridge → vnc_stream_connect → route_vnc_to_channel → QUIC → tunnel → vnc_endpoint → QEMU/Xvnc

---

## 一、链路概览

```
DeviceDesktopView (vncTarget, deviceStatus)
    │
    └─ createVncTransport(vncTarget)
           │
           ├─ transportCache 复用 (OPEN) → setTimeout(onopen)
           ├─ pendingByKey 并发去重
           └─ new VncBridgeTransport → connect()
                  │
                  └─ invoke('vnc_stream_connect') → stream_id
                         │
                         └─ vnc_stream.rs
                                ├─ evict_for_resource (有旧则 250ms 延迟)
                                ├─ 注册 streams / by_resource
                                └─ spawn route_vnc_to_channel
                                       │
                                       └─ vnc_proxy.route_vnc_to_channel
                                              ├─ get_or_create_local_conn (QUIC)
                                              ├─ open_vnc_stream
                                              └─ bridge_channel_quic (mpsc ↔ QUIC)
                                                     │
                                                     └─ tunnel.handle_incoming_stream
                                                            ├─ ensure_vnc_endpoint
                                                            └─ proxy_quic_to_unix
                                                                   │
                                                                   └─ QEMU/Xvnc Unix socket
```

---

## 二、逻辑正确性 ✅

### 2.1 前端

| 环节 | 逻辑 | 状态 |
|------|------|------|
| DeviceDesktopView effect | requestId 防竞态；maindesk 需 deviceStatus=running | ✅ |
| createVncTransport | 缓存复用 + pendingByKey 去重；超时 race | ✅ |
| VncBridgeTransport | connect 后 setupListeners 再 setTimeout(onopen) | ✅ |
| useVnc | prevTransport 切换时关闭；readyState 检查；unmount 时 disconnect | ✅ |

### 2.2 后端

| 环节 | 逻辑 | 状态 |
|------|------|------|
| evict_for_resource | 先 by_resource 再 streams；drop(tx) 触发 route 退出 | ✅ |
| 250ms 延迟 | had_old 时 sleep，缓解 maindesk 重连竞态 | ✅ |
| route 退出清理 | streams.remove + by_resource.retain | ✅ |
| 空闲驱逐 | 5s 轮询，30s 无 touch 则驱逐 | ✅ |
| 心跳 | bridge 每 20s touch，避免静止画面被驱逐 | ✅ |

### 2.3 连接池一致性

- `streams` 与 `by_resource` 通过 evict、route 退出、idle 任务三处统一维护
- 驱逐时先改 `by_resource` 再 `streams.remove`，避免短暂不一致导致误删

---

## 三、潜在问题与建议

### 3.1 中：touch 高频 spawn

**位置**：`vnc_stream.rs` 中 `touch` 闭包

```rust
move || {
    tauri::async_runtime::spawn(async move {
        let mut by = br.write().await;
        if let Some((_, ref mut last)) = by.get_mut(&rid) {
            *last = Instant::now();
        }
    });
}
```

**问题**：每次 channel→quic 或 quic→channel 都 spawn 一个任务，高流量时可能产生大量 spawn。

**建议**：对 touch 做节流（例如 100ms 内只执行一次），或改为 `try_write` 等非阻塞更新。

---

### 3.2 低：route 失败时前端可能收不到 close

**位置**：`vnc_stream.rs` spawn 中

```rust
Err(e) => {
    let _ = app_clone.emit(&close_event, &e.to_string());
}
```

**说明**：`emit` 失败时（例如前端已卸载）会静默忽略，一般可接受。若需更强保证，可考虑重试或日志。

---

### 3.3 低：vnc_stream_send 失败无重试

**位置**：`vncBridge.ts` send()

```ts
invoke('vnc_stream_send', ...).catch((err) => {
  console.warn('[VNC-FLOW] [1-Bridge] vnc_stream_send 失败', err);
});
```

**说明**：RFB 发送失败仅打日志，不重试。通常表示 stream 已关闭，重试意义不大，当前行为合理。

---

### 3.4 低：proxy 持锁范围

**位置**：`vnc_stream_connect` 中 `resolve_device_id` 与取 `handler_state`

```rust
let p = proxy.lock().await;  // resolve 期间持锁
// ...
let state = proxy.lock().await.handler_state.clone();  // 再次持锁
```

**说明**：持锁时间短，仅做读取，一般不会成为瓶颈。若后续有并发扩展需求，可考虑将 `handler_state` 单独管理以减少锁竞争。

---

## 四、竞态与边界

### 4.1 已覆盖

| 场景 | 处理 |
|------|------|
| maindesk 重连 | evict 后 250ms 延迟 |
| Strict Mode 双挂载 | pendingByKey 复用 promise |
| transport 切换 | doConnect 关闭 prevTransport |
| unmount | disconnect → transport.close |
| route 失败 | emit close_event + 清理注册表 |

### 4.2 边界

- **close 不调后端**：依赖 30s 空闲或新连接 eviction，设计如此。
- **local_conn 不随 stream 错误清除**：仅 Scrcpy 在 `open_scrcpy_stream` 失败时清除；VNC 未清除。若 QUIC 连接异常，可能复用坏连接。当前 QUIC 较稳定，可接受；若问题增多可考虑在 route 失败时清除。

---

## 五、数据流完整性

```
前端 send → vnc_stream_send → tx.send → channel_to_quic → quic_send
                                                              │
后端 recv ← Tauri emit(data) ← quic_to_channel ← quic_recv ←─┘
```

- channel 容量 64，背压通过 `tx.send` 自然体现
- base64 编解码仅在 emit 路径，不影响 RFB 语义

---

## 六、结论

整体逻辑正确，主要设计点（eviction、延迟、去重、心跳）已覆盖。建议优化：

1. **中**：touch 节流，降低高流量下的 spawn 数量
2. **低**：视需要增强 route 失败时的 close 可靠性或日志

其余为可接受的实现细节，无需立即修改。

---

*审计基于 2026-03 代码库*
