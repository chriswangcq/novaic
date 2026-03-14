# 连接池与 P2P 保活逻辑分析

## 1. 连接池如何保证不被被动断开？

### 当前机制

| 层级 | 机制 | 说明 |
|------|------|------|
| **应用层（VNC stream）** | 30s 空闲关闭 | 连接池主动关闭无活动的 stream，释放资源 |
| **QUIC 连接层** | 25s keepalive PING | 防止 NAT 映射老化，连接不会被网络被动断开 |
| **QUIC 连接缓存** | 4 分钟 TTL | vnc_proxy 的 local_conn / remote_conns 复用 QUIC 连接 |

### 关系

- **连接池关闭的是 VNC stream**（channel↔QUIC 的 bridge），不是 QUIC 连接
- QUIC 连接由 vnc_proxy 的 `get_or_create_local_conn` / `get_or_create_remote_conn` 缓存
- 关闭 stream 后，QUIC 连接仍可被后续 VNC 连接复用
- QUIC 层有 keepalive，连接本身不会被 NAT 被动断开

---

## 2. P2P 保活逻辑（已有）

### hole_punch.rs — `p2p_transport_config()`

```rust
// 5 分钟无数据才超时（VNC 看静止画面时长时间无流量）
t.max_idle_timeout(Some(
    quinn::IdleTimeout::from(quinn::VarInt::from_u32(300_000)), // 300_000 ms = 5 min
));
// 每 25s 发一次 PING，防止 NAT 映射老化（60s 内保活）
t.keep_alive_interval(Some(Duration::from_secs(25)));
```

### 使用位置

| 模块 | 用途 |
|------|------|
| `hole_punch::listen_for_peer` | PC 端 QUIC 服务端（本地直连） |
| `hole_punch::connect_to_peer` | 客户端直连（本地 loopback 127.0.0.1） |
| `relay::connect_via_relay` | Relay 客户端（远端连接） |

### 结论

- **P2P 已有 keepalive**：每 25s 发 PING，满足常见 NAT 60s 老化
- **idle 超时 5 分钟**：VNC 静止画面时允许较长时间无业务流量
- 本地直连和 relay 连接都使用同一 `p2p_transport_config()`

---

## 3. Relay 服务端（novaic-quic-service）

- Relay 使用 quinn 默认 `ServerConfig`，未显式设置 `transport_config`
- 客户端会每 25s 发 PING，服务端按 QUIC 协议自动回 PONG
- 保活由客户端驱动，服务端无需额外配置

---

## 4. 潜在问题与建议

### 4.1 连接池 30s 与 QUIC 5min 的差异

- 连接池 30s 无活动会关闭 **VNC stream**
- QUIC 连接 5min 无活动才会超时
- 若希望减少重连、提高复用，可将连接池空闲时间调大（例如 60s 或 90s），与 QUIC 保活策略更一致

### 4.2 静止画面下的「活动」定义

- `touch()` 在 `vnc_stream_send`（前端→后端）和 `quic_to_channel`（VNC 帧）时调用
- 静止画面时 VNC 可能很少发帧，`touch` 可能长时间不触发
- 若 30s 内既无输入也无新帧，连接池会关闭 stream
- 可考虑：在 `channel_to_quic` 收到数据时也调用 `touch`（当前已有），或增加周期性心跳

### 4.3 Relay 服务端显式配置（可选）

- 若希望 relay 端也显式设置 `max_idle_timeout` 和 `keep_alive_interval`，可与客户端保持一致
- 当前依赖 quinn 默认行为，一般已足够

---

## 5. 总结

| 问题 | 结论 |
|------|------|
| P2P 是否有 keepalive？ | **有**，25s 间隔 PING |
| 连接池会不会被被动断开？ | **不会**，QUIC 层 keepalive 防止 NAT 断开 |
| 谁在主动关闭？ | 连接池在 30s 无活动时关闭 **VNC stream**，不是 QUIC 连接 |
| QUIC 连接会复用吗？ | **会**，vnc_proxy 的 local_conn / remote_conns 缓存，TTL 4 分钟 |
