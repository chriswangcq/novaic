# novaic-quic-service 设计（简化版）

> **独立通用服务**：STUN（获取外网 IP）+ QUIC Relay（P2P 失败兜底）。可单独域名、单独机器。

---

## 一、策略

- **P2P 优先**：手机直连 PC（现有逻辑不变），PC 全锥型 NAT 时可成功
- **Relay 兜底**：P2P 超时(15s) 后自动走 relay，用户无感知
- **不做双向打洞**：手机侧难以接受入站，成功率低，不实现

---

## 二、目标与定位

1. **独立部署**：`novaic-quic-service` 可单独域名、单独机器
2. **STUN 服务**：从 Gateway 迁入，PC 通过 STUN 获取 ext_addr（原 api.gradievo.com，现 stun.gradievo.com）
3. **QUIC Relay**：接收 PC/手机 QUIC 连接，配对后转发 stream
4. **鉴权解耦**：Relay 通过 HTTP 调用 Gateway 校验 JWT，无共享状态

---

## 三、部署拓扑

```
┌──────────────────────────────────────────┐     ┌──────────────────────────────────────────┐
│  api.gradievo.com（Gateway）                │     │  stun.gradievo.com + relay.gradievo.com               │
│  - /api/p2p/*（心跳、locate、relay-request）│     │  - novaic-quic-service                  │
│  - /internal/pc/ws（CloudBridge）          │     │  - STUN UDP :3478，Relay HTTP/3 :443     │
│  - 不再跑 STUN                             │     └────────────────┬─────────────────────────┘
└────────────────┬─────────────────────────┘     └────────────────┬─────────────────────────┘
                 │                                                │
                 │  relay 鉴权时 HTTP 调用                         │  PC / 手机 QUIC
                 └────────────────────┬───────────────────────────┘
                                      │
                     ┌────────────────┼────────────────┐
                     │                │                │
                ┌────▼────┐    ┌─────▼─────┐    ┌─────▼────┐
                │   PC    │    │  Gateway  │    │  手机    │
                │ 信令←WS  │    │ relay-    │    │ relay-   │
                │ Relay→QUIC    │ request   │    │ request  │
                └─────────┘    └───────────┘    └─────────┘
```

---

## 四、连接流程

### 4.1 完整流程

```
手机 get_vnc_proxy_url
  → my-devices 取 device_id
  → punch_and_connect(PC.ext_addr)     # 现有逻辑
  → 成功: 直连 QUIC
  → 失败(15s 超时): 走 Relay

Relay 流程:
  1. 手机: POST /api/p2p/relay-request { target_device_id }
  2. Gateway: 校验 JWT、归属，推 connect_relay 给 PC
  3. Gateway: 返回 { relay_url, session_id } 给手机
  4. PC: 收到 connect_relay → 连接 relay
  5. 手机: 连接 relay
  6. relay: 配对，转发 stream
```

### 4.2 时序

```
手机                     Gateway                    PC                    relay
  │                         │                         │                      │
  │ punch_and_connect       │                         │                      │
  │ ─────────────────────────────────────────────────►│                      │
  │ (15s 超时)               │                         │                      │
  │                         │                         │                      │
  │ POST relay-request      │                         │                      │
  │ ───────────────────────►│                         │                      │
  │                         │ connect_relay (WS)      │                      │
  │                         │ ───────────────────────►│                      │
  │                         │                         │ QUIC RegisterPc      │
  │ { relay_url, session_id }│                         │ ──────────────────────────────────►
  │ ◄───────────────────────│                         │                      │
  │                         │                         │                      │
  │ QUIC ConnectRequest     │                         │                      │
  │ ───────────────────────────────────────────────────────────────────────►
  │                         │                         │                      │
  │                         │                         │        配对、转发     │
  │ ◄══════════════════════════════════════════════════════════════════════►
```

---

## 五、Gateway 变更

### 5.1 新增接口

| 接口 | 说明 |
|------|------|
| `POST /api/p2p/relay-request` | 手机请求 relay。Body: `{ target_device_id }`。校验 JWT、device 归属后，推 connect_relay 给 PC，返回 `{ relay_url, session_id }` |

### 5.2 CloudBridge 新增消息

| 消息 | 方向 | 说明 |
|------|------|------|
| `connect_relay` | Gateway → PC | `{ "type": "connect_relay", "relay_url": "https://relay.xxx.com/p2p/relay", "session_id": "uuid" }`。PC 收到后连接 relay（无端口，443 默认） |

### 5.3 配置

- `RELAY_URL`：relay 地址，如 `https://relay.xxx.com/p2p/relay`（无端口，443 默认）

---

## 六、QUIC Relay 协议

### 6.1 连接建立

- 若需 nginx 按 path 转发，Relay 需基于 HTTP/3：首请求 `POST /p2p/relay`，后续 stream 复用该连接

```
PC 侧:
  - 连接 relay: https://relay.xxx.com/p2p/relay（HTTP/3，无端口）
  - 首包/首 stream: RegisterPc { device_id, jwt, session_id }
  - relay 校验 JWT，建立 device_id + session_id → Connection

手机侧:
  - 连接 relay: https://relay.xxx.com/p2p/relay（HTTP/3，无端口）
  - 首包/首 stream: ConnectRequest { target_device_id, jwt, session_id }
  - relay 校验 JWT，按 session_id 配对 PC 连接
  - 配对成功 → 转发 stream；否则 "PC offline" 或 "session expired"
```

### 6.2 流复用

- 复用现有 `p2p::tunnel`：`open_vnc_stream(agent_id)`, `open_scrcpy_stream(serial)`
- relay 将 PC 与手机的 QUIC stream 按 stream_id 双向转发

### 6.3 鉴权

- relay 调用 `GET Gateway/internal/auth/validate`（带 JWT）
- 校验 device_id 归属 user_id

---

## 七、novaic-quic-service 结构

```
novaic-quic-service/
├── Cargo.toml
├── src/
│   ├── main.rs
│   ├── config.rs      # LISTEN_PORT=443, GATEWAY_URL
│   ├── auth.rs        # JWT 校验（调 Gateway）
│   ├── relay.rs       # 连接配对、stream 转发
│   ├── protocol.rs    # RegisterPc, ConnectRequest 等
│   ├── stun.rs        # RFC 5389 STUN 服务（从 gateway 迁入）
│   └── lib.rs
└── README.md
```

### 7.1 端口与路径

**端口约定**：
- **Relay**：`https://relay.xxx.com/p2p/relay`，443 默认（HTTPS 标准）
- **STUN**：`stun.gradievo.com`，3478 默认（RFC 5389 标准）

**方案 A：双端口（标准）**
- STUN UDP 3478，Relay HTTP/3 UDP 443
- 客户端：STUN `stun.gradievo.com`（3478 隐式），Relay `https://relay.gradievo.com/p2p/relay`（443 隐式）

**方案 B：路径 + nginx 转发（推荐）**
- **Relay**：使用 HTTP/3（QUIC + HTTP），路径 `/p2p/relay`。nginx 按 path 转发到 relay 后端（需 relay 协议基于 HTTP/3）
- **STUN**：UDP 无 path 概念，可选子域名 + 独立端口，或与 Relay 同端口由 novaic-quic-service 按协议区分

---

## 八、与 Gateway 的边界

| 职责 | Gateway | novaic-quic-service |
|------|---------|---------------------|
| P2P 心跳/locate | ✅ | - |
| relay-request | ✅ | - |
| connect_relay 推送 | ✅ | - |
| STUN（获取 ext_addr） | ❌ 迁出 | ✅ |
| QUIC relay | - | ✅ |
| JWT 校验 | ✅ | 调用 Gateway |

---

## 九、部署（独立）

- **域名**：如 `relay.gradievo.com`，与 api 分离
- **机器**：可单独申请
- **端口**：STUN UDP 3478（标准），Relay HTTP/3 UDP 443
- **配置**：`GATEWAY_URL`, `LISTEN_PORT`（默认 443）

### 9.1 客户端配置变更

- **novaic-app**：STUN `stun.gradievo.com`（3478 标准默认），Relay `https://relay.gradievo.com/p2p/relay`（443 默认）
- **Gateway**：不再部署 STUN，api.gradievo.com 可关闭 STUN 端口

### 9.2 nginx 转发示例

**方案 1：Relay 用 path（推荐）**
- `relay.xxx.com:443`：HTTP/3，按 path `/p2p/relay` 转发到 relay 后端
- STUN 与 Relay 同机部署时，可由 novaic-quic-service 单进程按协议区分，或 STUN 用独立端口 3478 由 nginx 转发

```nginx
# relay.xxx.com:443 - HTTP/3 按 path 转发
server {
    listen 443 udp reuseport;
    ssl_protocols TLSv1.3;
    # ... ssl_certificate ...
    location /p2p/relay {
        proxy_pass https://127.0.0.1:19999;  # relay 后端
        proxy_http_version 3;
    }
}
```

**方案 2：STUN 标准端口**
- STUN 监听 3478（RFC 5389 标准），客户端 `stun.gradievo.com` 隐式 3478
