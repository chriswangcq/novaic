# novaic-quic-service 实施计划（按模块）

> 基于 `DESIGN-novaic-quic-service.md`，按模块拆分的详细实施步骤。

---

## 一、模块总览

| 模块 | 路径 | 依赖 | 预估 |
|------|------|------|------|
| 1. novaic-quic-service（新建） | `novaic-quic-service/` | - | 核心 |
| 2. Gateway | `novaic-gateway/` | 1 部分完成 | 中 |
| 3. novaic-app（p2p） | `novaic-app/src-tauri/p2p/` | 1 部署 | 中 |
| 4. novaic-app（vmcontrol） | `novaic-app/src-tauri/vmcontrol/` | 3 | 小 |
| 5. novaic-app（vnc_proxy） | `novaic-app/src-tauri/src/` | 3, 4 | 中 |
| 6. 部署与文档 | `docs/`, `nginx/` | 1–5 | 小 |

---

## 二、模块 1：novaic-quic-service（新建）

### 2.1 项目骨架

```
novaic-quic-service/
├── Cargo.toml
├── src/
│   ├── main.rs
│   ├── lib.rs
│   ├── config.rs
│   ├── stun.rs
│   ├── relay.rs
│   ├── protocol.rs
│   └── auth.rs
└── README.md
```

**步骤：**

1. `cargo new novaic-quic-service --bin`
2. 添加依赖：`tokio`, `quinn`, `rustls`, `reqwest`, `serde`, `serde_json`, `tracing`, `anyhow`
3. `config.rs`：从环境变量读取 `GATEWAY_URL`, `LISTEN_PORT`（默认 443）, `RELAY_BACKEND_PORT`（内部）

### 2.2 STUN 模块（stun.rs）

**职责**：RFC 5389 STUN 服务，返回 XOR-MAPPED-ADDRESS。

**步骤：**

1. 参考 `novaic-gateway/scripts/stun_server.py` 逻辑，用 Rust 实现
2. 监听 UDP socket，解析 Binding Request（首 20 字节），构造 Binding Response
3. 导出 `run_stun_server(socket: UdpSocket) -> impl Future`，在收到包时回复

**协议要点**：
- Request: type=0x0001, length=0, magic=0x2112A442, 12B transaction_id
- Response: type=0x0101, XOR-MAPPED-ADDRESS(0x0020), 端口/IP 与 magic XOR

### 2.3 Relay 模块（relay.rs + protocol.rs）

**职责**：HTTP/3 服务，路径 `/p2p/relay`，接收 PC RegisterPc 与手机 ConnectRequest，配对后转发 stream。

**步骤：**

1. **protocol.rs**：定义 JSON 消息
   - `RegisterPc { device_id, jwt, session_id }`
   - `ConnectRequest { target_device_id, jwt, session_id }`
   - `ConnectResponse { ok, error? }`

2. **auth.rs**：调用 Gateway `GET /internal/auth/validate`（带 JWT），校验 device_id 归属

3. **relay.rs**：
   - 使用 `h3` + `quinn` 或 `quinn` 裸流 + 自定义 HTTP 解析
   - 监听 path `/p2p/relay` 的 POST 请求，body 为 RegisterPc 或 ConnectRequest
   - 维护 `session_id -> (device_id, Connection)` 映射
   - PC 连接：校验 JWT → 存映射
   - 手机连接：校验 JWT → 按 session_id 找 PC → 配对
   - 配对后：复用 `p2p::tunnel` 的 stream 协议（0x01 VNC, 0x02 Scrcpy），双向转发

4. **main.rs**：
   - 方案 A：单 UDP 443，首包 demux（STUN 固定头 vs QUIC）→ 分发给 stun 或 relay
   - 方案 B：两个端口，STUN 3478 + Relay 19999，由 nginx 统一入口

### 2.4 入口与启动

**main.rs**：

```rust
// 1. 解析 config
// 2. 若单端口：创建 UDP socket 443，spawn demux task
// 3. demux：读首 20 字节，若 STUN(0x0001) -> stun handler，否则 -> relay (QUIC)
// 4. stun handler：回复后继续读
// 5. relay：将 socket 交给 quinn Endpoint 处理 HTTP/3
```

---

## 三、模块 2：Gateway

### 3.1 新增 `POST /api/p2p/relay-request`

**文件**：`novaic-gateway/gateway/api/p2p.py`

**步骤：**

1. 定义 `RelayRequestRequest { target_device_id }`, `RelayRequestResponse { relay_url, session_id }`
2. 校验 JWT（已有 `get_current_user`）
3. 校验 `target_device_id` 在 `_p2p_registry` 且 `user_id` 一致
4. 生成 `session_id = uuid4()`
5. 获取 `RELAY_URL`（如 `https://relay.xxx.com/p2p/relay`）
6. 调用 `send_push_to_device(target_device_id, "connect_relay", { relay_url, session_id })`
7. 返回 `{ relay_url, session_id }`

### 3.2 新增 `send_push_to_device`（无响应推送）

**文件**：`novaic-gateway/gateway/api/internal/pc_client.py`

**步骤：**

1. 新增 `async def send_push_to_device(device: DeviceState, msg_type: str, payload: dict) -> None`
2. 不创建 `_pending` future，直接 `ws.send_json({"type": msg_type, **payload})`
3. 用于 `connect_relay` 等单向通知

### 3.3 配置

**文件**：`novaic-gateway/` 配置或环境变量

- `RELAY_URL`：`https://relay.xxx.com/p2p/relay`

### 3.4 Gateway 鉴权接口（供 relay 调用）

**文件**：`novaic-gateway/gateway/api/auth.py` 或 `p2p.py`

- 已有 `GET /internal/auth/validate`：校验 JWT，返回 `X-User-ID`
- 新增 `GET /internal/auth/validate-device?device_id=xxx`：Header `Authorization: Bearer <jwt>`，校验 JWT 得 user_id，再查 `_p2p_registry` 中 device_id 是否归属该 user_id，返回 200 或 401

---

## 四、模块 3：novaic-app p2p

### 4.1 STUN 默认服务器迁移

**文件**：`novaic-app/src-tauri/p2p/src/rendezvous.rs`

**步骤：**

1. `STUN_SERVER_DEFAULT` 从 `api.gradievo.com:443` 改为 `stun.gradievo.com:3478`（RFC 5389 标准端口）
2. 新增 `ensure_stun_port()`：若配置未含端口，自动补 `:3478`
3. `NOVAIC_STUN_SERVER` 可覆盖，如 `stun.l.google.com:19302` 或 `stun.gradievo.com`（自动 3478）

### 4.2 新增 relay 连接逻辑（hole_punch.rs）

**文件**：`novaic-app/src-tauri/p2p/src/hole_punch.rs`

**步骤：**

1. 新增 `connect_via_relay(relay_url: &str, jwt: &str, session_id: &str, role: RelayRole) -> Result<Connection>`
2. `RelayRole::Pc { device_id }`：连接 relay，发送 RegisterPc
3. `RelayRole::Mobile { target_device_id }`：连接 relay，发送 ConnectRequest
4. 使用 HTTP/3 或 QUIC 裸连接，解析 `relay_url`（如 `https://relay.xxx.com/p2p/relay`）得到 host + path
5. 建立 QUIC 连接（relay 的 TLS 证书需校验，可用系统 CA 或固定证书）
6. 首 stream 发送 JSON 注册/连接请求，等待配对成功

### 4.3 新增 punch_or_relay（punch 超时后走 relay）

**文件**：`novaic-app/src-tauri/p2p/src/hole_punch.rs`

**步骤：**

1. 新增 `punch_or_relay(gateway_url, jwt, target_device_id, relay_url, session_id) -> Result<Connection>`
2. 先调用 `punch_and_connect`（15s 超时）
3. 若成功 → 返回 P2P 连接
4. 若超时 → 调用 Gateway `POST /api/p2p/relay-request` 获取 `relay_url, session_id`（若调用方已提供则跳过）
5. 调用 `connect_via_relay` 建立 relay 连接

**注意**：`relay-request` 由手机发起，Gateway 推 `connect_relay` 给 PC。因此流程为：
- 手机：punch 超时 → 调 relay-request → 拿 relay_url+session_id → connect_via_relay(Mobile)
- PC：收到 connect_relay → connect_via_relay(Pc)

---

## 五、模块 4：novaic-app vmcontrol（CloudBridge）

### 5.1 处理 connect_relay 消息

**文件**：`novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs`

**步骤：**

1. 在 `IncomingMessage` 中新增 `ConnectRelay { relay_url: String, session_id: String }`
2. 收到后：调用 `p2p::hole_punch::connect_via_relay(relay_url, jwt, session_id, RelayRole::Pc { device_id })`
3. 将建立的 `Connection` 存入某处，供后续 VNC/scrcpy 使用（需与 VncProxy 共享）
4. 可选：发送 `connect_relay_ack` 给 Gateway（当前设计不要求）

### 5.2 共享 Relay 连接

**问题**：CloudBridge 收到 connect_relay 时建立连接，但 VncProxy 的 `get_or_create_remote_conn` 走的是 punch_and_connect。

**方案**：

1. 新增 `SharedRelayConnections: Arc<RwLock<HashMap<String, (Connection, Instant)>>>`，key = session_id 或 target_device_id
2. CloudBridge 收到 connect_relay 后，建立连接并写入 `SharedRelayConnections`
3. VncProxy 的 `get_or_create_remote_conn` 先查 `SharedRelayConnections`，若有且未过期则用，否则走 punch
4. 需在 Tauri 主进程或 VmControl 启动时注入该共享状态

---

## 六、模块 5：novaic-app vnc_proxy

### 6.1 修改 get_or_create_remote_conn

**文件**：`novaic-app/src-tauri/src/vnc_proxy.rs`

**步骤：**

1. 当前逻辑：`punch_and_connect` → 成功则缓存
2. 新逻辑：
   - 先查 `SharedRelayConnections`（若存在）
   - 若无，调用 `punch_or_relay`：
     - 先 `punch_and_connect`（15s）
     - 超时则 `relay-request` → 等待 PC 侧 CloudBridge 收到 connect_relay 并建连
     - 手机侧 `relay-request` 返回后 `connect_via_relay`
   - 问题：`relay-request` 是手机调用的，PC 不会调。所以流程是：
     - 手机：`punch_and_connect` 超时 → `relay-request` → 拿到 relay_url+session_id → `connect_via_relay`
     - PC：CloudBridge 收到 connect_relay → `connect_via_relay`（PC 先连还是手机先连？设计上 PC 先收到推送，先连；手机拿到 relay_url 后连。relay 端配对 session_id。）

3. **简化**：`get_or_create_remote_conn` 只负责手机侧。手机侧流程：
   - `punch_and_connect` 超时
   - `relay-request` 获取 relay_url, session_id
   - `connect_via_relay` 建立连接
   - PC 侧由 CloudBridge 在收到 connect_relay 时建连，连接需与手机配对

4. **共享状态**：手机和 PC 是不同端。手机是 Tauri Mobile，PC 是桌面。所以：
   - 手机端 `get_or_create_remote_conn`：punch 超时 → relay-request → connect_via_relay
   - PC 端：CloudBridge 在 PC 上运行，收到 connect_relay → connect_via_relay，并将 Connection 存起来
   - PC 端 VncProxy：当有 VNC 请求时，若已有 relay 连接（由 connect_relay 建立），则复用

5. **关键**：PC 的 VncProxy 和 CloudBridge 同进程。CloudBridge 收到 connect_relay 后建立的 Connection 需要给 VncProxy 用。所以需要 `SharedRelayConnections` 或类似结构，key 为 `target_device_id`（手机端）或 `device_id`（PC 端）。配对时 session_id 相同，所以可以用 session_id 做 key。但 VncProxy 的 `get_or_create_remote_conn(device_id)` 的 device_id 是目标 PC 的 device_id。所以：
   - PC 端：connect_relay 的 payload 有 relay_url, session_id。PC 的 device_id 是自身。建立连接后，应以 (session_id, device_id) 或 session_id 存，因为一个 session 对应一次 relay 请求。
   - 手机端：relay-request 返回 relay_url, session_id。connect_via_relay 时用 session_id 配对。手机要连的是 target_device_id（PC）。
   - 所以：`SharedRelayConnections`: `HashMap<device_id, Connection>`，表示「到某 PC 的 relay 连接」。但 relay 是 session 维度的，一个 session 对应一次「手机-PC」配对。所以 PC 端存 `session_id -> Connection`，当 VncProxy 要连 device_id 时，需要知道哪个 session_id 对应该 device_id。relay-request 是手机为连 target_device_id 发起的，Gateway 推给该 target_device_id 的 PC。所以 PC 收到 connect_relay 时，session_id 和 relay_url 已知，建连后，该连接就是「手机要连的那台 PC」的连接。PC 端可以存 `session_id -> Connection`，但 VncProxy 的 key 是 device_id。所以需要在 connect_relay 时，PC 知道「这是为我的 device_id 建的」，存 `device_id -> Connection` 即可（因为一台 PC 同时只有一个 relay session 在连？不，可能多个手机连同一 PC？每个 session 不同。所以是 `session_id -> Connection`，而 VncProxy 请求时，需要 session_id。但 VncProxy 的入口是 device_id，不是 session_id。
   - 重新理解：手机要连 PC（device_id）。punch 失败，走 relay。手机调 relay-request(target_device_id)，Gateway 推 connect_relay 给 PC，返回 session_id 给手机。PC 和手机各自连 relay，用 session_id 配对。所以从手机视角，`get_or_create_remote_conn(device_id)` 要拿到「到 device_id 的 QUIC 连接」。若走 relay，这个连接是经 relay 的。手机不知道 session_id 和 relay 的对应关系，是 relay-request 返回的。所以流程：
     - 手机 `get_or_create_remote_conn(device_id)`：
       1. punch_and_connect(device_id) 超时
       2. relay-request(device_id) → relay_url, session_id
       3. connect_via_relay(relay_url, session_id, Mobile{target_device_id: device_id})
       4. 得到 Connection，缓存到 remote_conns[device_id]
     - PC 端：CloudBridge 收到 connect_relay(relay_url, session_id)，此时 target 就是本 PC。PC connect_via_relay(relay_url, session_id, Pc{device_id})。建连后，该 Connection 要能被 VncProxy 使用。但 PC 的 VncProxy 的 `get_or_create_remote_conn` 是「手机调用的」，即手机要连 PC 时，是手机端的 VncProxy。PC 端 VncProxy 是「本机 VmControl」或「作为被连端」。所以：
     - 手机端：有 VncProxy，要连远端 PC，所以 get_or_create_remote_conn(device_id) 是手机调用的。
     - PC 端：有 VncProxy，但本机时走 local，远端时是「手机连 PC」的场景，所以 PC 的 VncProxy 的 remote 路径是「手机连我」？不，看代码：serve_remote_vnc 是「连远端 device 的 VNC」，所以是手机连 PC。即手机运行 VncProxy，请求 device_id=PC 的 VNC，所以 get_or_create_remote_conn(PC_device_id) 在手机执行。
   - 结论：`get_or_create_remote_conn` 只在手机端执行。PC 端不需要 get_or_create_remote_conn 去连别人，PC 是被连端。所以：
     - 手机：punch 超时 → relay-request → connect_via_relay → 缓存
     - PC：CloudBridge 收到 connect_relay → connect_via_relay，建立 Connection。这个 Connection 是「PC 作为 relay 的一端」。relay 会配对 PC 和手机的连接，所以 PC 的 Connection 和手机的 Connection 在 relay 内部配对。PC 端建连后，需要把这个 Connection 交给谁？交给「处理来自手机的 VNC 请求」的逻辑。但 VNC 请求是经 QUIC stream 来的，即手机 open_vnc_stream 后，数据会到 PC。PC 的 PunchListener.accept() 会收到 QUIC 连接。若走 relay，连接不是到 PunchListener，而是到 relay 再转发到 PC。所以 PC 的 relay 连接建立后，relay 会把手机的 stream 转发给 PC 的 Connection。PC 端需要像 PunchListener 一样，从 Connection 上 accept stream。所以 PC 端 CloudBridge 建连后，要把 Connection 交给「处理 relay 连接的逻辑」，类似 run_tunnel_server，即从 Connection 上 accept_bi，处理 VNC/scrcpy stream。所以 PC 端不是「VncProxy get_or_create_remote_conn」，而是「有一个 relay 连接池」，当 connect_relay 时建连，然后 spawn run_tunnel_server(relay_conn, vmcontrol_base_url)。这样 relay 来的 stream 会被正确路由到 VmControl。

6. **修正理解**：PC 端收到 connect_relay 后，建立到 relay 的 Connection，然后 spawn `run_tunnel_server(conn, vmcontrol_base_url)`，这样 relay 转发过来的 VNC/scrcpy stream 会被处理。不需要 SharedRelayConnections 给 VncProxy 用，因为 relay 连接是「入站」的，stream 由 run_tunnel_server 处理。手机端是「出站」，需要 connect_via_relay 拿到 Connection，然后 open_vnc_stream。

---

## 七、模块 5（续）：vnc_proxy 修改

### 7.1 手机端 get_or_create_remote_conn

**步骤：**

1. 先 `punch_and_connect`（15s）
2. 超时则：
   - `POST /api/p2p/relay-request` body `{ target_device_id }`
   - 解析返回 `{ relay_url, session_id }`
   - `connect_via_relay(relay_url, jwt, session_id, Mobile { target_device_id })`
   - 缓存 Connection 到 `remote_conns[device_id]`

### 7.2 PC 端 CloudBridge 处理 connect_relay

**步骤：**

1. 收到 `ConnectRelay { relay_url, session_id }`
2. `conn = connect_via_relay(relay_url, jwt, session_id, Pc { device_id })`
3. `tokio::spawn(run_tunnel_server(conn, vmcontrol_base_url))`

---

## 八、模块 6：部署与文档

### 8.1 novaic-quic-service 部署

- systemd 或 docker
- 环境变量：`GATEWAY_URL`, `LISTEN_PORT`, `RELAY_URL`（若自配置）
- 证书：TLS 证书（若 HTTP/3）

### 8.2 nginx 配置

- relay.xxx.com:443 UDP → 按 path `/p2p/relay` 转发到 novaic-quic-service
- STUN：同端口 demux 或子域名

### 8.3 文档更新

- `STUN_SERVER_DEPLOY.md`：STUN 迁至 novaic-quic-service
- `DESIGN-novaic-quic-service.md`：补充实施细节

---

## 九、实施顺序建议

| 阶段 | 模块 | 可并行 |
|------|------|--------|
| 1 | novaic-quic-service 骨架 + STUN | - |
| 2 | novaic-quic-service Relay 协议 + auth | 依赖 1 |
| 3 | Gateway relay-request + send_push | 可与 2 并行 |
| 4 | p2p rendezvous STUN 默认值 | 可与 2 并行 |
| 5 | p2p hole_punch connect_via_relay | 依赖 2 |
| 6 | CloudBridge connect_relay 处理 | 依赖 3, 5 |
| 7 | vnc_proxy punch_or_relay 流程 | 依赖 5, 6 |
| 8 | 部署 + 文档 | 依赖 1–7 |

---

## 十、测试要点

1. **STUN**：PC 端 `get_external_addr` 用 stun.gradievo.com 能拿到正确 ext_addr
2. **Relay 鉴权**：无效 JWT 被拒绝
3. **Relay 配对**：PC 先连、手机后连，stream 能双向转发
4. **端到端**：手机 VNC 连接，P2P 失败时自动走 relay，画面正常
