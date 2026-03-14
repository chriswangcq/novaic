# Phase 3 任务分工 — 4 名工程师

> 基于 `DESIGN-novaic-quic-service.md` 与 `DESIGN-novaic-quic-service-IMPLEMENTATION.md`。  
> Phase 3 目标：新建 novaic-quic-service（STUN + Relay），Gateway 新增 relay-request，客户端 punch_or_relay 兜底。

---

## 一、总览

| 工程师 | 模块 | 依赖 | 预估 |
|--------|------|------|------|
| **A** | novaic-quic-service 骨架 + STUN | - | 3–4 天 |
| **B** | novaic-quic-service Relay（protocol/auth/relay） | A 骨架 | 4–5 天 |
| **C** | Gateway relay-request + send_push + validate-device | - | 2–3 天 |
| **D** | p2p connect_via_relay + CloudBridge + vnc_proxy | B, C | 4–5 天 |

**并行策略**：A 与 C 可同时开工；B 等 A 骨架完成；D 等 B、C 完成。

---

## 二、工程师 A：novaic-quic-service 骨架 + STUN

### 2.1 产出

- 新建 `novaic-quic-service/` 项目
- 实现 RFC 5389 STUN 服务
- 支持单端口 demux（STUN vs QUIC）或双端口部署

### 2.2 任务清单

1. **项目骨架**
   - `cargo new novaic-quic-service --bin`
   - `Cargo.toml`：`tokio`, `tracing`, `anyhow`, `serde`, `serde_json`
   - `src/main.rs`, `src/lib.rs`, `src/config.rs`

2. **config.rs**
   - 环境变量：`GATEWAY_URL`, `LISTEN_PORT`（默认 443）, `STUN_PORT`（默认 3478）
   - 支持双端口（STUN 3478 + Relay 443）或单端口 demux

3. **stun.rs**
   - 解析 Binding Request（type=0x0001, magic=0x2112A442）
   - 构造 Binding Response，XOR-MAPPED-ADDRESS(0x0020)
   - `run_stun_server(socket: UdpSocket) -> impl Future`
   - 参考 `novaic-gateway/scripts/stun_server.py`（如有）

4. **main.rs 启动**
   - 方案 A：双端口 — STUN 3478，Relay 443（B 实现后接入）
   - 方案 B：单端口 demux — 读首 20 字节，STUN(0x0001) → stun handler，否则 → relay

5. **README.md**
   - 部署说明、环境变量、端口约定

### 2.3 验收

- `cargo run` 启动后，`stun.gradievo.com:3478` 可返回正确 XOR-MAPPED-ADDRESS
- p2p `get_external_addr` 使用 `NOVAIC_STUN_SERVER=stun.gradievo.com:3478` 能拿到外网地址

---

## 三、工程师 B：novaic-quic-service Relay

### 3.1 产出

- protocol.rs：RegisterPc, ConnectRequest, ConnectResponse
- auth.rs：调用 Gateway 校验 JWT
- relay.rs：HTTP/3 服务，配对 PC/手机，转发 stream

### 3.2 任务清单

1. **protocol.rs**
   - `RegisterPc { device_id, jwt, session_id }`
   - `ConnectRequest { target_device_id, jwt, session_id }`
   - `ConnectResponse { ok, error? }`
   - serde 序列化

2. **auth.rs**
   - `validate_jwt(gateway_url, jwt) -> Result<user_id>`
   - 调用 `GET {gateway_url}/internal/auth/validate`，Header `Authorization: Bearer <jwt>`
   - 解析 `X-User-ID` 或等价响应

3. **relay.rs**
   - 使用 `h3` + `quinn` 或 quinn 裸流 + 自定义 HTTP 解析
   - 监听 `POST /p2p/relay`，body 为 RegisterPc 或 ConnectRequest
   - `session_id -> (device_id, Connection)` 映射
   - PC：校验 JWT → 存映射
   - 手机：校验 JWT → 按 session_id 找 PC → 配对
   - 配对后：复用 p2p tunnel 协议（0x01 VNC, 0x02 Scrcpy），双向转发 stream

4. **main.rs 集成**
   - 启动 Relay HTTP/3 服务（443 或 RELAY_BACKEND_PORT）
   - 与 A 的 STUN 协同（双端口或 demux）

### 3.3 验收

- 无效 JWT 被拒绝
- PC 先连、手机后连，stream 能双向转发
- 端到端：手机 VNC 经 relay 可显示画面

---

## 四、工程师 C：Gateway 变更

### 4.1 产出

- `POST /api/p2p/relay-request`
- `send_push_to_device`（无响应推送）
- `GET /internal/auth/validate-device`（供 relay 调用）

### 4.2 任务清单

1. **relay-request**
   - 文件：`novaic-gateway/gateway/api/p2p.py`
   - 请求：`RelayRequestRequest { target_device_id }`
   - 响应：`RelayRequestResponse { relay_url, session_id }`
   - 校验 JWT、`target_device_id` 在 `_p2p_registry` 且 `user_id` 一致
   - 生成 `session_id = uuid4()`
   - 从配置取 `RELAY_URL`（如 `https://relay.gradievo.com/p2p/relay`）
   - 调用 `send_push_to_device(target_device_id, "connect_relay", { relay_url, session_id })`
   - 返回 `{ relay_url, session_id }`

2. **send_push_to_device**
   - 文件：`novaic-gateway/gateway/api/internal/pc_client.py` 或等价
   - 根据 `target_device_id` 找到 PC 的 WebSocket 连接
   - 发送 `{"type": "connect_relay", "relay_url": "...", "session_id": "..."}`
   - 无响应、无 pending future

3. **validate-device**
   - 文件：`novaic-gateway/gateway/api/auth.py` 或 `internal/`
   - `GET /internal/auth/validate-device?device_id=xxx`
   - Header `Authorization: Bearer <jwt>`
   - 校验 JWT 得 user_id，查 `_p2p_registry` 中 device_id 是否归属该 user_id
   - 返回 200 或 401

4. **配置**
   - 环境变量 `RELAY_URL`：`https://relay.gradievo.com/p2p/relay`

### 4.3 验收

- 手机调用 relay-request 后，PC 收到 connect_relay 推送
- relay 调用 validate-device 能正确校验 device 归属

---

## 五、工程师 D：p2p + CloudBridge + vnc_proxy

### 5.1 产出

- p2p `connect_via_relay`、`punch_or_relay`
- CloudBridge 处理 `connect_relay`
- vnc_proxy `get_or_create_remote_conn` 走 punch_or_relay

### 5.2 任务清单

1. **p2p hole_punch.rs**
   - `connect_via_relay(relay_url, jwt, session_id, RelayRole) -> Result<Connection>`
   - `RelayRole::Pc { device_id }`：连接 relay，发送 RegisterPc
   - `RelayRole::Mobile { target_device_id }`：连接 relay，发送 ConnectRequest
   - 使用 HTTP/3 或 QUIC 裸连接，解析 relay_url 得到 host + path
   - `punch_or_relay(gateway_url, jwt, target_device_id, ...) -> Result<Connection>`
     - 先 `punch_and_connect`（15s 超时）
     - 超时 → `POST /api/p2p/relay-request` → `connect_via_relay`

2. **CloudBridge cloud_bridge.rs**
   - `IncomingMessage` 新增 `ConnectRelay { relay_url, session_id }`
   - 收到后：`p2p::hole_punch::connect_via_relay(..., RelayRole::Pc { device_id })`
   - `tokio::spawn(run_tunnel_server(conn, vmcontrol_base_url))`

3. **vnc_proxy**
   - 文件：`novaic-app/src-tauri/src/vnc_proxy.rs` 或等价
   - `get_or_create_remote_conn`：先 `punch_and_connect`，超时则 `punch_or_relay`
   - 缓存 Connection 到 `remote_conns[device_id]`

### 5.3 验收

- P2P 成功时直连，失败时自动走 relay
- 手机 VNC 连接，P2P 失败后经 relay 可正常显示画面
- PC 收到 connect_relay 后能建立 relay 连接并处理 stream

---

## 六、实施顺序与里程碑

```
Week 1:
  A: 骨架 + STUN 完成
  C: relay-request + send_push + validate-device 完成
  B: 等 A 骨架 → 开始 protocol/auth/relay

Week 2:
  B: Relay 完成，与 A 集成
  D: 等 B、C → 开始 connect_via_relay、CloudBridge、vnc_proxy

Week 3:
  D: 完成，端到端联调
  部署 + 文档
```

---

## 七、接口约定（跨工程师）

### 7.1 relay-request（C → D）

- 手机调用：`POST /api/p2p/relay-request` body `{ "target_device_id": "..." }`
- 返回：`{ "relay_url": "https://relay.xxx.com/p2p/relay", "session_id": "uuid" }`
- PC 收到：`connect_relay { relay_url, session_id }` via WebSocket

### 7.2 Relay 协议（B ↔ D）

- PC：`RegisterPc { device_id, jwt, session_id }`
- 手机：`ConnectRequest { target_device_id, jwt, session_id }`
- 响应：`ConnectResponse { ok: true }` 或 `{ ok: false, error: "..." }`

### 7.3 STUN（A ↔ p2p）

- 默认：`stun.gradievo.com:3478`（RFC 5389）
- 环境变量：`NOVAIC_STUN_SERVER` 可覆盖

---

## 八、参考文档

| 文档 | 说明 |
|------|------|
| `DESIGN-novaic-quic-service.md` | STUN + Relay 服务设计 |
| `DESIGN-novaic-quic-service-IMPLEMENTATION.md` | 按模块实施计划 |
| `phase3-p2p-remote.md` | P2P 打洞与 tunnel 协议 |
