# VNC 稳定性缺口与改进建议（Round 3）

**产出时间**: 2026-03-12  
**输入**: `docs/survey-2026/VNC_RELAY_ROUND1.md`、`VNC_PROXY_ROUTING_ROUND2.md`、`vnc_proxy.rs`、`vnc_bridge.rs`、`vnc_endpoint.rs`、`tunnel.rs`、`main.tsx`

---

## 1. 缺口：ensure_vnc_endpoint 超时无 Close reason

### 1.1 问题描述

`ensure_vnc_endpoint` 在 subuser 场景下轮询 port 文件，超时 30s 后返回明确错误：

```rust
// vnc_endpoint.rs:168-173
return Err(format!(
    "VNC port file not found for user '{}': {} — Xvnc may not have started (timeout {}s)",
    username, port_file, SUBUSER_POLL_TIMEOUT_SECS
));
```

该错误发生在 **PC 侧**（tunnel server），传播链如下：

| 层级 | 行为 |
|------|------|
| `ensure_vnc_endpoint` | 返回 `Err("VNC port file not found for user 'xxx': ... — Xvnc may not have started (timeout 30s)")` |
| `tunnel::handle_incoming_stream` | 重试 3 次后 `return Err(last_err)`，task 退出 |
| PC 侧 stream handler | QUIC stream 被 drop，**不向 QUIC 写入错误消息** |
| VncProxy 侧 `bridge_ws_quic` | `quic_recv.read()` 收到 EOF/reset，loop 退出 |
| `WsWriteCloseGuard` drop | 调用 `sink.close()`，**无 reason** |

### 1.2 根因

- PC 侧 tunnel 在 `ensure_vnc_endpoint` 失败时仅关闭 QUIC stream，未通过 QUIC 协议向 VncProxy 传递错误文本
- VncProxy 的 `bridge_ws_quic` 仅感知「QUIC 流结束」，无法区分「正常结束」与「ensure_vnc_endpoint 超时」
- `WsWriteCloseGuard` 在 drop 时只做 `sink.close()`，不附带自定义 reason

### 1.3 影响

- 前端收到 abrupt close，无具体错误文案
- 用户无法区分「Xvnc 未启动 / port 文件超时」与「网络断开」「设备离线」等
- 可诊断性与用户体验受损

---

## 2. 缺口：bridge_ws_quic 中 QUIC 断开无 Close reason

### 2.1 问题描述

`bridge_ws_quic` 运行中，当 QUIC 连接或 stream 因以下原因断开时：

- PC 端 VmControl 退出
- 网络中断（NAT 超时、Wi-Fi 切换等）
- Xvnc / VM 崩溃导致 proxy_quic_to_unix 退出
- QUIC connection 被对端关闭

`quic_recv.read()` 或 `quic_send.write_all()` 返回 Err，loop 退出，`WsWriteCloseGuard` drop 时仅执行 `sink.close()`，**不附带 reason**。

### 2.2 代码路径

```rust
// vnc_proxy.rs:458-469
let quic_to_ws = async {
    let mut buf = vec![0u8; 65536];
    loop {
        match quic_recv.read(&mut buf).await {
            Ok(Some(n)) if n > 0 => { /* ... */ }
            _ => break,   // EOF / Err 时直接 break，无 reason
        }
    }
    Ok::<(), anyhow::Error>(())
};

// WsWriteCloseGuard Drop: vnc_proxy.rs:419-424
fn drop(&mut self) {
    if let Some(mut sink) = self.0.take() {
        tauri::async_runtime::spawn(async move {
            let _ = sink.close().await;  // 无 CloseFrame.reason
        });
    }
}
```

### 2.3 与 ensure_vnc_endpoint 的关系

两者共用同一 `bridge_ws_quic` 路径：无论是「建立前 ensure_vnc_endpoint 超时」还是「建立后 QUIC 断开」，VncProxy 侧都只能感知「QUIC 流结束」，无法获取具体错误，因此均无法发送带 reason 的 Close 帧。

### 2.4 影响

- 用户看到「连接意外断开」，无法区分设备离线、Xvnc 崩溃、网络问题等
- 重试策略无法根据错误类型做差异化（如 Xvnc 未启动应提示等待，网络问题可自动重连）

---

## 3. 远端 + subuser 30s 可能不足

### 3.1 时序分析

| 阶段 | 本机 | 远端 |
|------|------|------|
| `get_or_create_*_conn` | ~100ms（QUIC loopback） | **10–30s**（Gateway locate + relay + QUIC） |
| `open_vnc_stream` | ~50ms | ~50ms |
| PC 侧 `ensure_vnc_endpoint` | 0（maindesk）或 0–30s（subuser） | **0–30s**（subuser 轮询 port） |

### 3.2 最坏叠加

- **远端 + subuser + port 未就绪**：P2P 建连 10–30s + ensure_vnc_endpoint 0–30s ≈ **10–60s**
- 当前 `WS_UPGRADE_TIMEOUT = 30s`，极易在 ensure_vnc_endpoint 尚未返回时触发超时
- 即便 ensure_vnc_endpoint 成功，若 P2P 建连接近 30s，也可能在 `open_vnc_stream` 或 `bridge_ws_quic` 建立前被 30s 超时打断

### 3.3 参考

- `VNC_BACKEND_TUNNEL_TIMING_REPORT.md` §3.4：远端 + subuser 且 port 未就绪时，P2P + ensure_vnc_endpoint 叠加很容易超过 30s
- `VNC_STABILITY_RECONNECT_RESEARCH_ROUND3.md`：30s 可能不足，建议延长或动态设置

---

## 4. 控制台噪音过滤现状（main.tsx suppress）

### 4.1 实现

```typescript
// main.tsx:8-28
// noVNC: 过滤预期内的控制台噪音
// - Disconnection timed out: WebSocket 关闭握手 3s 内未完成时触发
// - Failed when connecting / Connection closed: 切换 Agent 或桥接关闭时的级联提示
// - Unexpected server disconnect: 连接过程中服务端关闭
if (typeof window !== 'undefined' && window.console?.error) {
  const _ce = window.console.error.bind(window.console);
  const suppress = (msg: unknown) => {
    const s = String(msg ?? '');
    return (
      s.includes('Disconnection timed out') ||
      s.includes('Failed when connecting') ||
      s.includes('Failed when disconnecting') ||
      s.includes('Unexpected server disconnect')
    );
  };
  window.console.error = (...args: unknown[]) => {
    const toCheck = args.length > 0 ? args[0] : '';
    if (suppress(toCheck)) return;
    _ce(...args);
  };
}
```

### 4.2 过滤模式

| 模式 | 来源 | 说明 |
|------|------|------|
| `Disconnection timed out` | noVNC | WebSocket 关闭握手 3s 内未完成 |
| `Failed when connecting` | noVNC | 连接建立失败（切换 Agent、桥接关闭等） |
| `Failed when disconnecting` | noVNC | 断开过程失败 |
| `Unexpected server disconnect` | noVNC | 服务端主动关闭连接 |

### 4.3 现状与局限

- **优点**：减少预期内错误的控制台噪音，避免用户/开发者被大量重复日志干扰
- **局限**：
  - 仅做字符串包含匹配，可能误伤其他包含相同子串的合法错误
  - 无环境开关（如 `sessionStorage.novaic_ota_debug`）控制是否过滤，调试时需改代码
  - 未覆盖 `Connection closed`（vnc_bridge.rs 默认 reason）等变体
  - 过滤后错误完全消失，无法通过 console 追溯问题，仅依赖 UI 展示的 `errorMsg`

### 4.4 与 Close reason 的关系

若后端能正确发送 Close reason（如 "VNC connection timed out (30s)"、"VNC port file not found..."），前端可通过 `e?.detail?.reason` 展示给用户。控制台 suppress 仅影响 `console.error` 输出，不影响 UI 错误展示。两者互补：suppress 减少噪音，Close reason 保证用户可见的错误信息。

---

## 5. 改进建议

### 5.1 高优先级

| 建议 | 说明 | 涉及文件 |
|------|------|----------|
| **ensure_vnc_endpoint 错误透传到 VncProxy** | 在 QUIC 流协议中增加「错误消息」机制：PC 侧 tunnel 在 ensure_vnc_endpoint 失败时，在关闭 stream 前写入简短错误文本（如 1 字节类型 + 变长 reason），VncProxy 侧 bridge_ws_quic 解析后调用 `send_ws_close_with_reason` | `tunnel.rs`、`vnc_proxy.rs`、`p2p` 协议 |
| **bridge_ws_quic QUIC 断开时发送 Close reason** | 在 `quic_to_ws` 和 `ws_to_quic` 分支退出时，区分 EOF / Err，构造语义化 reason（如 "VNC session ended (device or Xvnc stopped)"、"Connection reset"），在 drop WsWriteCloseGuard 前调用 `send_ws_close_with_reason` | `vnc_proxy.rs` |
| **延长 WS_UPGRADE_TIMEOUT（远端 + subuser）** | 将 30s 调整为 60s，或根据 `is_remote` + `resource_id.contains(':')` 动态设置（远端 subuser 用 60s） | `vnc_proxy.rs` |

### 5.2 中优先级

| 建议 | 说明 | 涉及文件 |
|------|------|----------|
| **控制台 suppress 可配置** | 当 `sessionStorage.novaic_ota_debug === '1'` 时跳过 suppress，便于调试 | `main.tsx` |
| **noVNC patch 透传 Close reason** | 按 `P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md` 对 `@novnc/novnc` 打 patch，使 `disconnect` 事件 `detail` 含 `reason`，前端 `useVnc.ts`、`vncStream.ts` 可展示 | `patches/@novnc+novnc` |
| **vnc_bridge_connect 超时** | OTA 下 `invoke('vnc_bridge_connect')` 无显式超时，P2P 建连可能 10–30s，建议 `Promise.race` 30–60s 超时 | `vncBridge.ts` |

### 5.3 低优先级

| 建议 | 说明 |
|------|------|
| **结构化错误码** | 在 Close 帧或自定义协议中携带错误码，便于前端区分「超时」「Xvnc 未启动」「设备离线」等，做差异化重试/提示 |
| **suppress 白名单细化** | 仅对 noVNC 特定错误做 suppress，避免误伤其他模块的 `console.error` |
| **tunnel 重试与 WS 超时协调** | 减少 tunnel 的 `VNC_RETRY_ATTEMPTS` 或缩短单次 `ensure_vnc_endpoint` 超时，避免 3×30s 与 vnc_proxy 30s 脱节 |

---

## 6. 参考

| 文档 | 关联内容 |
|------|----------|
| `VNC_RELAY_ROUND1.md` | 连接决策、ensure_vnc_endpoint 概览 |
| `VNC_PROXY_ROUTING_ROUND2.md` | 错误传播链、Close reason 调用点、未覆盖场景 |
| `VNC_BACKEND_TUNNEL_TIMING_REPORT.md` | 30s 超时分析、远端+subuser 时序 |
| `VNC_STABILITY_RECONNECT_RESEARCH_ROUND3.md` | 超时与 Close reason、重试策略 |
| `P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md` | noVNC patch、reason 透传 |
| `11-phase4-vnc-stability-10-subagent-master-report.md` | P0-2 超时无 reason、30s 不足 |
