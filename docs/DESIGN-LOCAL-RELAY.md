# 桌面端内置本地 Relay 实施方案

> **说明**：relay URL 方案已搁置（AppInstance 中不再包含 self_relay_url）。本文档保留供日后参考。
>
> 原目标：PC 端启动时启动本地 relay，动态端口写入 AppInstance 并上报 Gateway；P2P 时若 Gateway 判断请求方与目标同属同一用户，则返回本地 relay URL。

---

## 一、概述

### 1.1 背景

- 当前 P2P 打洞失败时，手机通过云端 relay（relay.gradievo.com）连接 PC，需经公网，延迟较高
- 若 PC 与手机在同一用户账号下且 PC 在局域网内，可让 PC 运行本地 relay，手机直连 PC 的 relay，无需走云端

### 1.2 「同属」定义

- **同属一个 app_instance**：请求方（手机）与目标（PC）的 `user_id` 相同
- 即：同一用户账号下的两台设备（我的手机连我的 PC）

### 1.3 核心流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PC 启动                                                                   │
│    ├─ 启动本地 relay（0.0.0.0:0 → 动态端口）                                   │
│    ├─ 获取本机 LAN IP（如 192.168.1.100）                                     │
│    ├─ 构造 local_relay_url = "https://192.168.1.100:PORT"                     │
│    ├─ 写入 AppInstance.self_relay_url                                         │
│    └─ CloudBridge 连接时上报 x-local-relay-url                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Gateway 存储                                                              │
│    DeviceRegistry[device_id].local_relay_url = "https://192.168.1.100:PORT"   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. 手机 relay-request（target_device_id = PC）                                │
│    ├─ Gateway 校验：target 归属 user_id，且 target 有 local_relay_url          │
│    ├─ 判断「同属」：请求方 user_id == target user_id（同一用户）               │
│    └─ 返回 local_relay_url + session_id + cloud_relay_url（fallback）         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. 手机连接 local relay                                                      │
│    ├─ 成功：同 LAN，低延迟                                                      │
│    └─ 失败：fallback 云端 relay（用 cloud_relay_url 重试）                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. PC 收到 connect_relay 推送                                                 │
│    └─ 连接 relay_url（将 host 替换为 127.0.0.1 连自身 relay）                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 协议兼容性

本地 relay 与云端 relay（novaic-quic-service）**协议完全一致**：

- QUIC 握手
- 首行 JSON：`RegisterPc`（PC）或 `ConnectRequest`（手机）
- 鉴权：调用 Gateway `validate-device`、`validate-relay-session`
- 配对后 stream 转发

---

## 二、本地 Relay 服务设计

### 2.1 部署形态

**方案 A：内嵌到 Tauri 桌面 App（推荐）**

- 优点：与 VmControl、CloudBridge 同进程，无需额外进程
- 实现：在 `novaic-app` 中新增 `local_relay` 模块，复用 `novaic-quic-service` 的 relay 协议逻辑
- 依赖：`quinn`、`rustls`、`rcgen`（自签名）已在 `p2p` 或 `novaic-quic-service` 中

**方案 B：独立子进程**

- 优点：与主进程隔离，崩溃不影响主 App
- 缺点：需管理子进程生命周期、启动参数

**推荐方案 A**，与 VmControl 内嵌模式一致。

### 2.2 端口与绑定

| 参数 | 值 | 说明 |
|------|-----|------|
| 绑定地址 | `0.0.0.0:0` | 动态端口，由 OS 分配 |
| 监听范围 | 局域网内可访问 | 手机需能访问 PC 的 LAN IP |

> 若复用 `novaic-quic-service`，需扩展其 `Config` 支持 `relay_port=0`（`relay_bind_addr()` 返回 `0.0.0.0:0`）。

### 2.3 地址构造

- 本地 relay 绑定后，通过 `socket.local_addr()` 获取实际端口
- 本机 LAN IP：复用 `p2p::local_discovery::get_local_ipv4()` 或等价逻辑（UDP connect 到 8.8.8.8 取 local_addr）
- 构造 URL：`https://{lan_ip}:{port}`（QUIC 使用 443 语义，但本地可用任意端口）

### 2.4 TLS 证书

- 使用自签名证书（`rcgen`），与 novaic-quic-service 开发模式一致
- 本地 relay 不暴露公网，无需 Let's Encrypt
- 手机端连接时需 `NOVAIC_RELAY_INSECURE=1` 或等价配置以接受自签名（仅用于 local relay）

### 2.5 鉴权

- 与云端 relay 相同：调用 Gateway `GET /api/p2p/validate-device?device_id=xxx`、`GET /api/p2p/validate-relay-session?session_id=xxx&target_device_id=xxx`
- Gateway URL 从 `gateway_url.txt` 或环境变量读取

---

## 三、AppInstance 与上报

### 3.1 AppInstance 字段

已有 `self_relay_url: Option<String>`，需在本地 relay 启动后填充：

```rust
// 本地 relay 启动后
app_instance.write().await.self_relay_url = Some(format!("https://{}:{}", lan_ip, port));
```

### 3.2 上报 Gateway

**方式 A：CloudBridge WebSocket 握手时新增 header**

- 新增 `x-local-relay-url` header
- 与 `x-device-id`、`x-app-instance-id`、`x-machine-label` 一起发送
- 连接建立后若 relay 尚未就绪，可通过后续消息更新（需扩展协议）

**方式 B：WebSocket 连接建立后第一条消息**

- 新增消息类型 `local_relay_status { url: "https://..." }`
- Gateway 收到后更新 DeviceState

**推荐方式 A**：简单，与现有 header 模式一致。若 relay 启动晚于 CloudBridge 连接，可支持在后续 `ping` 或心跳响应中附带 `local_relay_url` 更新。

**方式 A 的时序**：若 relay 与 CloudBridge 同时启动，CloudBridge 可能先连上。需在 relay 就绪后「补报」：

- 在 CloudBridge 的 `pong` 响应或心跳中，若 `local_relay_url` 有值且未上报，可增加一次 `device_status` 类消息上报
- 或：CloudBridge 连接时若 relay 未就绪，先不传；relay 就绪后通过 `send_push_to_device` 的反向通道不可行（那是 Gateway→PC 的）。故需 **PC 主动上报**
- 方案：新增 Gateway 接口 `POST /api/p2p/update-local-relay`，PC 在 relay 就绪后调用，传入 `device_id`、`local_relay_url`，需 JWT 鉴权

**简化：** 调整启动顺序，让 **本地 relay 先于 CloudBridge 启动**，这样 CloudBridge 连接时 `local_relay_url` 已就绪，可直接通过 header 上报。

### 3.3 Gateway 存储

- `DeviceState` 新增 `local_relay_url: str = ""`
- 从 `x-local-relay-url` header 读取并写入
- 重连时更新

---

## 四、relay-request 逻辑改造

### 4.1 「同属」判断

- **定义**：请求方（手机）与目标（PC）的 `user_id` 相同
- **条件**：`relay-request` 的 `user_id`（来自 JWT）与 `target_device_id` 对应 P2PEntry 的 `user_id` 相同
- 满足时：若目标 PC 有 `local_relay_url`，优先返回

### 4.2 返回逻辑

```python
# 伪代码
if entry.user_id == user_id:  # 同属同一用户
    dev = registry.get_device(req.target_device_id)
    if dev and dev.local_relay_url:
        relay_url = dev.local_relay_url  # 优先本地
    else:
        relay_url = os.environ.get("RELAY_URL", "https://relay.gradievo.com/...")
else:
    relay_url = os.environ.get("RELAY_URL", ...)
```

### 4.3 连接失败 fallback

- 手机先尝试 `local_relay_url`，若连接失败（超时、TLS 错误等），应 **fallback 到云端 relay**
- 需二次调用 `relay-request` 或 Gateway 支持 `relay_url` 参数：第一次返回 `local_relay_url`，失败后客户端可请求「强制云端」：`relay-request?force_cloud=1`
- 或：Gateway 一次返回两个 URL：`relay_url`（优先）和 `cloud_relay_url`（fallback），客户端自行重试

**推荐**：`relay-request` 仅返回一个 `relay_url`。客户端首次用 `local_relay_url`（若有），失败后重新调用 `relay-request`，此时 Gateway 可带 `skip_local=1` 或根据策略返回云端（避免重复推同一 session 给 PC，需考虑 session 复用）。

**简化**：首次返回 `local_relay_url`，失败后客户端再调用一次 `relay-request`，Gateway 检测到同一 session 的短时重试则返回 `cloud_relay_url`。或更简单：Gateway 同时返回 `relay_url` 和 `cloud_relay_url`，客户端优先用 `relay_url`，失败用 `cloud_relay_url`，session_id 可复用。

---

## 五、手机端连接逻辑

### 5.1 relay-request 响应扩展

```json
{
  "relay_url": "https://192.168.1.100:19999",
  "cloud_relay_url": "https://relay.gradievo.com/p2p/relay",
  "session_id": "uuid-xxx"
}
```

- `relay_url`：优先使用（本地或云端）
- `cloud_relay_url`：fallback，始终为云端

### 5.2 连接顺序

1. 尝试连接 `relay_url`（可能是 local 或 cloud）
2. 超时（如 10s）或失败：连接 `cloud_relay_url`
3. session_id 不变，PC 端已收到 `connect_relay` 推送，会向云端 relay 注册；若手机走 local relay，PC 需向 local relay 注册

**注意**：PC 收到的 `connect_relay` 推送中的 `relay_url` 必须与手机一致。若 Gateway 给手机返回 `local_relay_url`，则推送的 `relay_url` 也应为 `local_relay_url`，PC 才会连到本地 relay。

**正确流程**：Gateway 推送 `connect_relay` 时，`relay_url` 与返回给手机的 `relay_url` 一致。若返回 `local_relay_url`，推送也是 `local_relay_url`。PC 和手机都连同一个 relay（本地 relay）。

**PC 连接自身 relay**：PC 收到 `relay_url=https://192.168.1.100:PORT` 时，可将 host 替换为 `127.0.0.1` 再连接（同机 loopback，避免绕网卡）。

---

## 六、实现步骤

### Phase 1：本地 Relay 模块（novaic-app）

**6.1 新增 `local_relay` 模块**

- 路径：`novaic-app/src-tauri/src/local_relay.rs` 或 `p2p/src/local_relay.rs`
- 复用方式二选一：
  - **A**：将 `novaic-quic-service` 改为 lib，`novaic-app` 依赖并调用 `run_relay_server`，传入自定义 `Config`（`relay_port=0`、`gateway_url`、自签名 cert）
  - **B**：将 relay 协议逻辑抽取到 `p2p` crate 的 `relay_server` 子模块，`novaic-quic-service` 与 `novaic-app` 共用

**6.2 启动时机**

- 在 `setup_shared` 或 VmControl 启动流程中，与 P2P 并行启动
- 先启动 relay，获取端口后再启动 CloudBridge（保证上报时 `local_relay_url` 已就绪）

**6.3 配置**

- `gateway_url`：从 `GatewayUrlState` 读取
- `bind_addr`：`0.0.0.0:0`
- TLS：自签名

### Phase 2：AppInstance 与上报

**6.4 更新 AppInstance**

- relay 就绪后：`app_instance.write().await.self_relay_url = Some(url)`

**6.5 CloudBridge 上报**

- `CloudBridgeConfig` 新增 `local_relay_url: Option<String>`
- 每次连接时在 header 中加 `x-local-relay-url`（若存在）

**6.6 Gateway 接收**

- `DeviceState` 新增 `local_relay_url`
- `pc_client_websocket` 读取 `x-local-relay-url` 并写入

### Phase 3：relay-request 改造

**6.7 Gateway**

- `relay-request`：若 `device.local_relay_url` 存在且 `entry.user_id == user_id`，返回 `local_relay_url`
- 响应增加 `cloud_relay_url` 字段供 fallback

**6.8 relay-request 推送**

- 推送 `connect_relay` 时，`relay_url` 与返回给手机的一致（即 local 或 cloud）

### Phase 4：手机端 fallback

**6.9 p2p relay 客户端**

- `connect_via_relay` 支持 `cloud_relay_url` 参数
- 首次连 `relay_url` 失败后，重试 `cloud_relay_url`

### Phase 5：本地 relay TLS

**6.10 手机端接受自签名**

- 连接 `local_relay_url` 时（host 为 LAN IP 或 localhost），使用 `NOVAIC_RELAY_INSECURE=1` 或针对非云端 host 自动跳过证书校验

---

## 七、依赖与复用

| 组件 | 复用/新增 |
|------|----------|
| 协议逻辑 | 从 `novaic-quic-service` 抽取或作为 lib 引入 |
| QUIC/TLS | `quinn`、`rustls`、`rcgen`（自签名） |
| Gateway 鉴权 | 现有 `validate-device`、`validate-relay-session` |
| LAN IP | `p2p::local_discovery::get_local_ipv4()` 或等价逻辑 |

---

## 八、风险与边界

1. **同 LAN 假设**：`local_relay_url` 使用 LAN IP，仅当手机与 PC 同 LAN 时有效；跨网时需 fallback 云端
2. **防火墙**：PC 需允许本地 relay 端口的入站连接
3. **多网卡**：`get_local_ipv4` 可能取到错误网卡，需测试或支持多网卡选择
4. **端口冲突**：动态端口可降低冲突概率

---

## 九、附录：协议与接口变更汇总

### A. CloudBridge 新增 header

| Header | 说明 |
|--------|------|
| `x-local-relay-url` | 本地 relay URL，如 `https://192.168.1.100:19999` |

### B. Gateway DeviceState 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `local_relay_url` | `str` | 从 `x-local-relay-url` 读取 |

### C. relay-request 响应扩展

| 字段 | 说明 |
|------|------|
| `relay_url` | 优先使用的 relay（本地或云端） |
| `cloud_relay_url` | 云端 relay，fallback 用 |

### D. connect_relay 推送

- `relay_url` 与返回给手机的 `relay_url` 一致
