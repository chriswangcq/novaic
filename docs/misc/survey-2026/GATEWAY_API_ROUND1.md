# NovAIC Gateway API 与职责边界调研（Round 1）

> 浅层调研：核心模块、vm/start vs devices/start、Gateway vs Tauri 职责、P2P 相关 API

**输入**：`novaic-gateway/`、`api.ts` gateway_get/post、`internal pc_client`

---

## 一、核心模块概览

| 模块 | 路径 | 职责 | 调用方 |
|------|------|------|--------|
| **agents** | `/api/agents` | Agent CRUD、binding、model、images、MCP 状态 | 前端 gateway_get/post |
| **devices** | `/api/devices` | 统一设备 API（Linux/Android）CRUD、start/stop/setup/status | 前端 gateway_get/post |
| **vm** | `/api/vm` | VM 生命周期（setup/start/stop）、环境检查、镜像、SSH、Android 代理 | 前端 gateway_get/post |
| **p2p** | `/api/p2p` | P2P 心跳、locate、relay-request、my-devices | Tauri、前端 |
| **internal** | `/internal/*` | 消息、subagent、agent、task、vm、config、health、pc_client | Tools Server、RO、Tauri CloudBridge |

### 1.1 agents 模块

- **文件**：`gateway/api/agents.py`
- **主要端点**：`GET/POST /api/agents`、`GET/PATCH/DELETE /api/agents/{id}`、`GET/PUT/DELETE /api/agents/{id}/binding`、`GET/PUT /api/agents/{id}/model`、`GET /api/agents/images`
- **依赖**：`get_pc_client_manager`（internal pc_client）用于 remove_vm_config、remove_android_config 时停止 VM/Android

### 1.2 devices 模块

- **文件**：`gateway/api/devices.py`
- **主要端点**：`GET/POST /api/devices`、`GET/PATCH/DELETE /api/devices/{id}`、`POST /api/devices/{id}/setup`、`POST /api/devices/{id}/start`、`POST /api/devices/{id}/stop`、`GET /api/devices/{id}/status`
- **依赖**：`get_pc_client_manager`（internal pc_client）用于 VM/Android 操作转发到 Tauri VmControl

### 1.3 vm 模块

- **文件**：`gateway/api/vm.py`
- **主要端点**：`GET /api/vm/environment`、`POST /api/vm/setup`、`POST /api/vm/start`、`POST /api/vm/stop`、`GET /api/vm/status/{agent_id}`、`POST /api/vm/deploy-wait`、`GET/POST /api/vm/android/*`
- **依赖**：`get_pc_client_manager` 转发所有 VM/Android 请求到 CloudBridge

### 1.4 p2p 模块

- **文件**：`gateway/api/p2p.py`
- **主要端点**：`POST /api/p2p/heartbeat`、`GET /api/p2p/locate/{device_id}`、`POST /api/p2p/relay-request`、`POST /api/p2p/relay-refresh-for-pc`、`GET /api/p2p/validate-relay-session`、`GET /api/p2p/my-devices`、`GET /api/p2p/validate-device`

### 1.5 internal 模块

- **文件**：`gateway/api/internal_proxy.py` + `gateway/api/internal/*.py`
- **子路由**：message、subagent、agent、task、vm、config、health、**pc_client**
- **pc_client**：`gateway/api/internal/pc_client.py` — DeviceRegistry、WebSocket `/internal/pc/ws`，Tauri CloudBridge 连接此端点

---

## 二、gateway_get/post 与 api.ts

### 2.1 Tauri 命令

| 命令 | 实现 | 说明 |
|------|------|------|
| `gateway_get` | `commands/gateway.rs` | `path` → `{base_url}{path}`，带 JWT |
| `gateway_post` | `commands/gateway.rs` | 同上，带 body |
| `gateway_get_impl` | 可测函数 | 供 vnc_urls、vnc_bridge 等直接调用 |

### 2.2 前端调用模式

```ts
// novaic-app/src/services/api.ts
invoke('gateway_get', { path: '/api/agents' })
invoke('gateway_post', { path: '/api/devices/{id}/start', body: {} })
```

- 前端所有 Gateway 请求均通过 `invoke('gateway_get/post/...')` 发起
- base URL 来自 `gateway_url.txt`（默认 `https://api.gradievo.com` 或本地 `127.0.0.1:19999`）

---

## 三、internal pc_client

### 3.1 职责

- **DeviceRegistry**：以 `device_id` 为键管理所有已连接 PC 的 WebSocket
- **WebSocket 端点**：`/internal/pc/ws`，Tauri App（CloudBridge）连接
- **握手头**：`x-device-id`、`x-user-id`、`x-app-instance-id`、`x-machine-label`

### 3.2 核心能力

| 能力 | 说明 |
|------|------|
| `forward_to_device` | 转发 HTTP 请求到 Tauri，等待 proxy_response |
| `send_push_to_device` | 单向推送（如 connect_relay） |
| `send_push_and_wait_ack` | 推送并等待 ACK（relay-request 用） |
| `get_pc_client_manager(user_id, pc_client_id?)` | 兼容接口，返回适配器，供 vm/devices/agents 调用 |

### 3.3 适配器

- `_DeviceManagerAdapter`：包装 DeviceState，提供 `vm_start`、`vm_shutdown`、`android_*` 等
- `_DisconnectedAdapter`：无连接时返回 ConnectionError

---

## 四、vm/start vs devices/start 区别

| 维度 | vm/start | devices/start |
|------|----------|---------------|
| **路径** | `POST /api/vm/start` | `POST /api/devices/{device_id}/start` |
| **主参数** | `agent_id`（body） | `device_id`（path） |
| **多 PC 参数** | ❌ 无 | `pc_client_id`（Query） |
| **语义** | Agent 维度：启动该 Agent 绑定的 VM | Device 维度：启动指定设备 |
| **device_id 解析** | `_resolve_vm_id_for_agent(agent_id)` → binding.device_id | 直接使用 path 中的 device_id |
| **PC 路由** | `get_pc_client_manager(user_id)` 取第一个 | `_get_pc_manager_for_device(device, user_id, pc_client_id)` |

### 4.1 调用链对比

```
vm/start:
  前端 vmService.start(agentId)
    → Gateway POST /api/vm/start { agent_id }
    → _resolve_vm_id_for_agent(agent_id) → vm_id
    → get_pc_client_manager(user_id)  ← 无 pc_client_id
    → pc_manager.vm_start(vm_id, body)
    → CloudBridge → Tauri VmControl

devices/start:
  前端 api.devices.start(deviceId, pcClientId?)
    → Gateway POST /api/devices/{device_id}/start?pc_client_id=xxx
    → _get_pc_manager_for_device(device, user_id, pc_client_id)
    → get_pc_client_manager(user_id, pc_client_id or device.pc_client_id)
    → mgr.vm_start(device.id, body)
    → CloudBridge → Tauri VmControl
```

### 4.2 差异总结

- **vm/start**：旧 Agent 中心流程，不支持多 PC
- **devices/start**：新 Device 中心流程，支持多 PC（`pc_client_id`）

---

## 五、Gateway vs Tauri 职责划分

| 职责 | Gateway | Tauri |
|------|:-------:|:-----:|
| REST API 编排 | ✅ | |
| VM/Device 启动编排 | ✅ | |
| VM 实际执行（QEMU/Android） | | ✅ VmControl |
| CloudBridge 服务端（/internal/pc/ws） | ✅ | |
| CloudBridge 客户端 | | ✅ |
| P2P 心跳、locate、my-devices | ✅ | |
| Relay 会话创建（relay-request） | ✅ | |
| Relay 会话校验（validate-relay-session） | ✅ | |
| Relay 连接建立 | | ✅ P2pClient |
| VNC 路由（本机/远端） | | ✅ vnc_proxy |
| VNC WebSocket 代理 | | ✅ |
| gateway_get/post 代理 | | ✅ 转发到 Gateway |

---

## 六、P2P 相关 API 详解

### 6.1 relay-request

| 项目 | 说明 |
|------|------|
| **路径** | `POST /api/p2p/relay-request` |
| **请求体** | `{ target_device_id: string }` |
| **用途** | 手机 P2P 打洞失败时调用，请求 relay 连接 |
| **流程** | 1. 校验 target_device_id 归属 user_id<br>2. 校验设备在 P2P 注册表且非 stale<br>3. 生成 session_id，推 `connect_relay` 给 PC（via DeviceRegistry）<br>4. 登记 PendingRelaySession<br>5. 返回 `{ relay_url, session_id }` |
| **依赖** | `get_device_registry`、`send_push_and_wait_ack` |

### 6.2 relay-refresh-for-pc

| 项目 | 说明 |
|------|------|
| **路径** | `POST /api/p2p/relay-refresh-for-pc` |
| **请求体** | `{ device_id: string }` |
| **用途** | PC 端重试 connect_via_relay 时，若 session 过期，调用此 API 续期 |
| **流程** | 1. 校验 device_id 归属<br>2. 查找 _device_to_session[device_id] → session_id<br>3. 若 pending 存在且未过期，重置 created_at<br>4. 返回 `{ ok, session_id, relay_url }` |
| **适用** | 仅当 validate_relay_session 因过期返回 404 时 |

### 6.3 validate-relay-session

| 项目 | 说明 |
|------|------|
| **路径** | `GET /api/p2p/validate-relay-session?session_id=xxx&target_device_id=xxx` |
| **用途** | Relay 服务调用：校验 session_id 是否由 relay-request 创建且未过期 |
| **流程** | 1. 查 _pending_relay_sessions[session_id]<br>2. 校验 target_device_id、user_id 一致<br>3. 校验未过期（_PENDING_SESSION_TTL_SECS=20s）<br>4. 过期则清理并返回 404 |
| **调用方** | Relay 服务（外部），需 JWT |

### 6.4 相关端点一览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/p2p/heartbeat` | POST | PC 心跳，更新 _p2p_registry |
| `/api/p2p/locate/{device_id}` | GET | 手机查询目标 PC 外网地址 |
| `/api/p2p/relay-request` | POST | 手机请求 relay，推 connect_relay 给 PC |
| `/api/p2p/relay-refresh-for-pc` | POST | PC 续期 relay session |
| `/api/p2p/validate-relay-session` | GET | Relay 校验 session |
| `/api/p2p/validate-device` | GET | Relay 校验 device_id 归属（公开，因 /internal 仅 127.0.0.1） |
| `/api/p2p/my-devices` | GET | 列出用户 P2P 设备，支持 current_app_instance_id、current_device_id |

---

## 七、参考文件

| 文件 | 说明 |
|------|------|
| `novaic-gateway/main_gateway.py` | 路由挂载、lifespan |
| `novaic-gateway/gateway/api/agents.py` | agents 模块 |
| `novaic-gateway/gateway/api/devices.py` | devices 模块 |
| `novaic-gateway/gateway/api/vm.py` | vm 模块 |
| `novaic-gateway/gateway/api/p2p.py` | p2p 模块 |
| `novaic-gateway/gateway/api/internal/pc_client.py` | DeviceRegistry、CloudBridge WS |
| `novaic-app/src/services/api.ts` | gateway_get/post 调用 |
| `novaic-app/src-tauri/src/commands/gateway.rs` | gateway_get/post 实现 |
| `docs/GATEWAY_VS_TAURI_RESPONSIBILITY_BOUNDARY_RESEARCH_ROUND3.md` | 深层职责边界 |
