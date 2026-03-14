# VNC 后端隧道与 Socket 时序分析报告

> 对照 `docs/unify-vnc/02-expert-design.md` §3.1、`docs/unify-vnc/03-maindesk-vs-subuser.md`，研究 Rust 后端 tunnel / vnc_proxy / vnc_endpoint 的时序、超时与错误传播。

---

## 一、tunnel.rs / find_vnc_target 与 ensure_vnc_endpoint

### 1.1 当前实现（已统一）

设计文档要求 `find_vnc_target` 简化为调用 `ensure_vnc_endpoint`。**当前实现已满足**：`tunnel.rs` 不再有独立的 `find_vnc_target`，直接调用 `vnc_endpoint::ensure_vnc_endpoint`。

| 类型 | resource_id | 目标 | 路径/来源 |
|------|-------------|------|-----------|
| **Maindesk** | `{vm_id}` | Unix socket | `/tmp/novaic/novaic-vnc-{vm_id}.sock`（QEMU 内置） |
| **Subuser** | `{vm_id}:{username}` | Unix 代理 | `/tmp/novaic/vnc-{vm_id}-{username}.sock` ← 代理到 `127.0.0.1:{port}` |

### 1.2 Subuser port 文件写入时序

**写入位置**：`vmcontrol/src/api/routes/users.rs` 中 `create_vm_user` 生成的 systemd 启动脚本。

**时序链**：

```
1. POST /api/vms/:id/users 创建子用户
2. systemctl start novaic-vnc-{username}.service
3. 启动脚本执行：
   a. 等待 9p mount /mnt/novaic-share（最多 60s）
   b. 启动 Xvnc：/usr/bin/Xvnc -rfbport $VNC_PORT ":N" &
   c. 轮询等待端口就绪（ss -ltn，最多 15s，0.5s 间隔）
   d. 写入 port 文件：echo $VNC_PORT > /mnt/novaic-share/vnc-{username}.port
   e. 启动 XFCE：dbus-run-session startxfce4 &
```

**9p 映射**：Guest `/mnt/novaic-share` ↔ Host `/tmp/novaic/share-{vm_id}/`，故 host 侧路径为 `/tmp/novaic/share-{vm_id}/vnc-{username}.port`。

**最坏延迟**：9p mount 60s + Xvnc 启动 ~2–5s + 端口轮询 15s ≈ 理论最大 ~80s，但实际 Xvnc 通常在 5–15s 内就绪。

**port 文件删除**：脚本末尾 `wait $XVNC_PID` 后执行 `rm -f "$PORT_FILE"`，即 Xvnc 退出时删除 port 文件。

---

## 二、ensure_vnc_endpoint 实现与设计符合度

### 2.1 设计要求（02-expert-design.md §3.1）

- VmControl 提供 `ensure_vnc_endpoint(resource_id) -> Result<SocketPath>`
- Subuser 场景：轮询等待 port 文件（**最多 30s，间隔 500ms**）
- 失败时返回明确错误（Xvnc 未启动、超时等）

### 2.2 当前实现（vnc_endpoint.rs）

| 项目 | 设计 | 实现 | 符合 |
|------|------|------|------|
| 超时 | 30s | `SUBUSER_POLL_TIMEOUT_SECS = 30` | ✅ |
| 轮询间隔 | 500ms | `SUBUSER_POLL_INTERVAL_MS = 500` | ✅ |
| 错误信息 | 明确（Xvnc 未启动、超时） | `"VNC port file not found for user '{}': {} — Xvnc may not have started (timeout {}s)"` | ✅ |

### 2.3 超时返回错误

```rust
// vnc_endpoint.rs:168-173
return Err(format!(
    "VNC port file not found for user '{}': {} — Xvnc may not have started (timeout {}s)",
    username, port_file, SUBUSER_POLL_TIMEOUT_SECS
));
```

**结论**：`ensure_vnc_endpoint` 与设计一致，超时返回明确错误。

---

## 三、vnc_proxy.rs：WS_UPGRADE_TIMEOUT 与阻塞分析

### 3.1 超时配置

```rust
// vnc_proxy.rs:63
const WS_UPGRADE_TIMEOUT: Duration = Duration::from_secs(30);
```

整个 `route_vnc`（含 `bridge_ws_quic`）被 30s 包裹：

```rust
// vnc_proxy.rs:184-187
match tokio::time::timeout(WS_UPGRADE_TIMEOUT, route_vnc(socket, ...)).await {
    Ok(Ok(())) => {}
    Ok(Err(e)) => tracing::error!("[VncProxy] Error ...");
    Err(_) => tracing::error!("[VncProxy] Timeout (30s) ...");
}
```

### 3.2 关键路径耗时（Subuser 场景）

| 阶段 | 本机 | 远端 |
|------|------|------|
| get_or_create_*_conn | ~100ms（QUIC loopback） | 10–30s（Gateway locate + relay + QUIC） |
| open_vnc_stream | ~50ms | ~50ms |
| **PC 侧 handle_incoming_stream** | | |
| └ ensure_vnc_endpoint | 0（maindesk socket 存在） | **0–30s**（subuser 轮询 port） |
| └ UnixStream::connect | ~10ms | ~10ms |
| └ proxy_quic_to_unix | 持续 | 持续 |

### 3.3 Subuser port 未就绪时的阻塞

- **阻塞点**：PC 侧 `ensure_vnc_endpoint` 轮询 port 文件，最长 30s。
- **阻塞位置**：`tunnel::handle_incoming_stream` 在 `ensure_vnc_endpoint` 返回前不会进入 `proxy_quic_to_unix`。
- **tunnel 阻塞时长**：与 `ensure_vnc_endpoint` 相同，最长 30s。

### 3.4 30s 超时是否足够

| 场景 | 典型耗时 | 是否可能超时 |
|------|----------|--------------|
| 本机 + maindesk | <1s | 否 |
| 本机 + subuser（port 已就绪） | <2s | 否 |
| 本机 + subuser（port 未就绪） | 0–30s | 可能刚好 30s |
| 远端 + maindesk | 10–30s（P2P）+ <1s | 可能超时 |
| 远端 + subuser（port 未就绪） | 10–30s + 0–30s | **极易超时** |

**结论**：远端 + subuser 且 port 未就绪时，P2P 建立（10–30s）与 `ensure_vnc_endpoint`（0–30s）叠加，很容易超过 30s。

### 3.5 超时后前端收到什么

- **30s 超时触发**：`tokio::time::timeout` 取消 `route_vnc` future。
- **WebSocket 状态**：已完成 upgrade，`bridge_ws_quic` 可能已在运行。
- **行为**：future 被 drop，WebSocket 句柄随之 drop，连接被强制关闭。
- **前端表现**：收到 abrupt close，通常无带 reason 的 Close 帧，表现为「连接意外断开」而非「超时」提示。

**建议**：超时前主动 `send_ws_close_with_reason`，例如 `"VNC connection timed out (30s)"`，便于前端展示明确错误。

---

## 四、open_vnc_stream 与崩溃检测

### 4.1 连接建立后的数据流

```
前端 WS ←→ vnc_proxy bridge_ws_quic ←→ QUIC stream ←→ PC tunnel proxy_quic_to_unix
                                                              ↓
                                        maindesk: Unix socket ←→ QEMU VNC
                                        subuser:  Unix socket ←→ handle_proxy_connection ←→ TCP 127.0.0.1:{port} ←→ Xvnc
```

### 4.2 VM / Xvnc 中途崩溃时的检测

| 崩溃点 | 传播链 | 前端是否收到断开 |
|--------|--------|------------------|
| **Xvnc 进程退出** | TCP RST → `tcp_read.read` Err/0 → `handle_proxy_connection` 退出 → Unix EOF → `proxy_quic_to_unix` 的 `unix_read` 返回 0 → `quic_send.finish()` → 手机侧 `quic_recv.read` Ok(None) → `bridge_ws_quic` break → `WsWriteCloseGuard` drop 发送 Close | ✅ 会断开 |
| **VM 完全崩溃** | QEMU 退出 → maindesk Unix 关闭；subuser 的 hostfwd 消失 → TCP RST，同上 | ✅ 会断开 |
| **PC 端 VmControl 退出** | QUIC 连接断开 → `quic_recv.read` Err → bridge break | ✅ 会断开 |

### 4.3 实现细节（handle_proxy_connection）

```rust
// vnc_endpoint.rs:283-294
let tcp_to_unix = async {
    loop {
        match tcp_read.read(&mut buf).await {
            Ok(0) => break,   // EOF
            Ok(n) => unix_write.write_all(&buf[..n]).await?,
            Err(_) => break,  // RST / 连接错误
        }
    }
    let _ = unix_write.shutdown().await;
    ...
};
```

TCP 读错误或 EOF 会正确传播到 Unix，进而到 QUIC，最终到前端。

### 4.4 断开时前端的错误信息

- **建立前失败**（如 `ensure_vnc_endpoint` 超时、`open_vnc_stream` 失败）：会调用 `send_ws_close_with_reason`，前端可拿到具体错误。
- **建立后崩溃**：`bridge_ws_quic` 中 `quic_recv.read` 得到 EOF/Err 后 break，`WsWriteCloseGuard` 只做 `sink.close()`，不附带自定义 reason。
- **结果**：前端收到的是通用 WebSocket close，没有「Xvnc 已崩溃」等语义化信息。

---

## 五、tunnel.rs 重试逻辑

```rust
// tunnel.rs:98-124
const VNC_RETRY_ATTEMPTS: u32 = 3;
const VNC_RETRY_DELAY_MS: u64 = 200;

for attempt in 0..VNC_RETRY_ATTEMPTS {
    match ensure_vnc_endpoint(&resource_id).await {
        Ok(socket_path) => {
            // UnixStream::connect with CONNECT_TIMEOUT_SECS=5
            ...
        }
        Err(msg) => last_err = Some(...),
    }
    if attempt < VNC_RETRY_ATTEMPTS - 1 {
        tokio::time::sleep(Duration::from_millis(VNC_RETRY_DELAY_MS)).await;
    }
}
```

- **ensure_vnc_endpoint**：每次调用最多 30s。
- **最坏情况**：3 × (30s + 5s) + 2 × 0.2s ≈ **105s**，远超 vnc_proxy 的 30s。
- **实际**：vnc_proxy 的 30s 会先触发，tunnel 的重试在超时前通常只完成 1 次。

---

## 六、修复建议

### 6.1 高优先级

| 建议 | 说明 |
|------|------|
| **WS 超时前发送 Close reason** | 在 `route_vnc` 外包一层，超时前主动 `send_ws_close_with_reason("VNC connection timed out (30s)")`，再取消 future，避免 abrupt close。 |
| **延长 WS_UPGRADE_TIMEOUT** | 远端 + subuser 场景建议 60s，或根据 `is_remote + subject_type` 动态设置。 |
| **建立后断开的 Close reason** | 在 `bridge_ws_quic` 中，当 `quic_recv` 因 EOF/Err 退出时，先 `send_ws_close_with_reason` 再 drop，例如 `"VNC session ended (device or Xvnc stopped)"`。 |

### 6.2 中优先级

| 建议 | 说明 |
|------|------|
| **ensure_vnc_endpoint 与 WS 超时协调** | 若 `ensure_vnc_endpoint` 设计为 30s，可将 WS 超时设为 35–40s，为 P2P 预留少量余量。 |
| **tunnel 重试与总超时** | 考虑减少 tunnel 重试次数，或缩短单次 `ensure_vnc_endpoint` 超时，避免与 vnc_proxy 超时脱节。 |

### 6.3 低优先级

| 建议 | 说明 |
|------|------|
| **Registry 校验 port 文件** | 设计文档建议：subuser 从 registry 命中时，校验 port 文件仍存在；若不存在则移除并重新轮询。当前实现已有类似逻辑（vnc_endpoint.rs:146-154）。 |
| **结构化错误码** | 考虑在 Close 帧或自定义协议中携带错误码，便于前端区分「超时」「Xvnc 未启动」「设备离线」等。 |

---

## 七、关键路径小结

```
前端 connect(ws://.../vnc/{pc_client_id}/{resource_id})
    ↓
vnc_proxy route_vnc [30s 总超时]
    ↓
get_or_create_*_conn  [本机 ~100ms | 远端 10–30s]
    ↓
open_vnc_stream  [~50ms]
    ↓
bridge_ws_quic 开始
    ↓
PC tunnel handle_incoming_stream
    ↓
ensure_vnc_endpoint  [maindesk 即时 | subuser 0–30s]
    ↓
UnixStream::connect [5s 超时] 或 proxy 建立
    ↓
proxy_quic_to_unix / handle_proxy_connection
    ↓
[运行中] VM/Xvnc 崩溃 → TCP RST → 传播 → 前端收到断开
```

---

## 八、相关文件索引

| 文件 | 职责 |
|------|------|
| `novaic-app/src-tauri/p2p/src/tunnel.rs` | QUIC stream 路由、ensure_vnc_endpoint 调用、proxy_quic_to_unix |
| `novaic-app/src-tauri/p2p/src/vnc_endpoint.rs` | ensure_vnc_endpoint、subuser 代理、port 轮询 |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | WS 代理、route_vnc、bridge_ws_quic、WS_UPGRADE_TIMEOUT |
| `novaic-app/src-tauri/vmcontrol/src/api/routes/users.rs` | 子用户创建、Xvnc 启动脚本、port 文件写入 |
| `novaic-app/src-tauri/vmcontrol/src/api/routes/vm.rs` | VM 启动、9p share、hostfwd、shutdown_proxy_for_vm 调用 |
