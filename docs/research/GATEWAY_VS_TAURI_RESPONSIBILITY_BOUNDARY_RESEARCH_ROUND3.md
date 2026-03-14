# 第三轮调研：Gateway 与 Tauri 的职责边界

> 深层调研：VNC 路由、relay 决策、vm/start vs devices/start 语义、internal vs 公开 API 边界

---

## 一、职责边界总览

| 领域 | Gateway | Tauri |
|------|---------|-------|
| **VNC 路由决策** | 无（不参与） | ✅ 全权：`route_vnc` 本机 vs 远端 |
| **Relay 决策** | 提供 relay-request、validate-relay-session | ✅ 执行：P2pClient::connect → relay |
| **VM/Device 启动** | ✅ 编排、转发到 Tauri | ✅ 实际执行（VmControl） |
| **PC 路由（多 PC）** | ✅ devices API 支持 pc_client_id | ✅ vnc_proxy 本机判断、P2P target |
| **P2P 注册表** | ✅ heartbeat、locate、my-devices | ✅ 上报 heartbeat |
| **CloudBridge** | ✅ /internal/pc/ws 接收连接 | ✅ CloudBridge 连接、转发请求 |
| **VNC 代理** | 无 | ✅ vnc_proxy WebSocket、QUIC 桥接 |

---

## 二、逻辑归属明细

### 2.1 VNC 路由

| 逻辑 | 位置 | 说明 |
|------|------|------|
| 本机 vs 远端判断 | **Tauri** `vnc_proxy.rs` `route_vnc` | `device_id == local_vmcontrol.device_id` → 本机 QUIC loopback |
| 远端连接建立 | **Tauri** `get_or_create_remote_conn` | `P2pClient::connect` → relay |
| 本地连接建立 | **Tauri** `get_or_create_local_conn` | `connect_direct(127.0.0.1:19998)` |
| VNC URL 构造 | **Tauri** `get_vnc_proxy_url` | `ws://127.0.0.1:{port}/vnc/{pc_client_id}/{resource_id}` |
| pc_client_id 解析 | **Tauri** | 桌面：`local_vmcontrol.device_id`；移动端：Gateway `my-devices` 第一个 online |
| Gateway 参与 | **无** | VNC 流量不经过 Gateway，仅 my-devices 供 Tauri 解析目标 PC |

### 2.2 Relay 决策

| 逻辑 | 位置 | 说明 |
|------|------|------|
| 打洞已移除 | **Tauri** `relay.rs` | 直接 `connect_via_relay` |
| relay-request | **Gateway** `p2p.py` | 手机调用 → 校验 target_device_id → 推 connect_relay 给 PC |
| relay session 校验 | **Gateway** `validate-relay-session` | Relay 服务调用，校验 session_id |
| 实际 relay 连接 | **Tauri** `relay::connect_via_relay` | QUIC 连接 relay 服务 |
| P2P 心跳 | **Gateway** `p2p.py` heartbeat | 接收 Tauri/VmControl 心跳，更新 `_p2p_registry` |
| P2P locate | **Gateway** `p2p.py` locate | 手机查询目标 PC 外网地址（打洞已移除，locate 仍存在但 relay 为主路径） |

### 2.3 VM/Device 启动

| 逻辑 | 位置 | 说明 |
|------|------|------|
| vm/start 编排 | **Gateway** `vm.py` | 解析 agent_id → device_id，构造 body，转发到 pc_manager |
| devices/start 编排 | **Gateway** `devices.py` | 校验 device 归属，调用 `_start_linux_device` / `_start_android_device` |
| 实际 VM 启动 | **Tauri** VmControl | 通过 CloudBridge 转发，Tauri 内嵌 VmControl 执行 QEMU |
| 多 PC 路由（devices） | **Gateway** | `_get_pc_manager_for_device(device, user_id, pc_client_id)` |
| 多 PC 路由（vm） | **Gateway** | ❌ **缺失**：`get_pc_client_manager(user_id)` 无 pc_client_id，始终取第一个 |

---

## 三、vm/start 与 devices/start 语义差异

### 3.1 参数与语义

| 维度 | vm/start | devices/start |
|------|----------|---------------|
| **路径** | `POST /api/vm/start` | `POST /api/devices/{device_id}/start` |
| **主参数** | `agent_id`（body） | `device_id`（path） |
| **多 PC 参数** | ❌ 无 | `pc_client_id`（Query） |
| **语义** | Agent 维度：启动该 Agent 绑定的 VM | Device 维度：启动指定设备 |
| **device_id 解析** | `_resolve_vm_id_for_agent(agent_id)` → binding.device_id | 直接使用 path 中的 device_id |

### 3.2 agent_id vs device_id

| 概念 | 含义 | 使用场景 |
|------|------|----------|
| **agent_id** | AIC Agent 的 UUID | vm/start、vm/stop、vm/status；Agent 与 Device 通过 binding 关联 |
| **device_id** | 设备 ID（Linux VM 时与 vm_id 同义） | devices/start、VNC resource_id（maindesk）、binding.device_id |
| **pc_client_id** | 物理 PC 标识（VmControl Ed25519 hex） | 多 PC 路由：devices API、VNC URL、P2P target |

### 3.3 调用链对比

```
vm/start:
  前端 vmService.start(agentId)
    → Gateway POST /api/vm/start { agent_id }
    → _resolve_vm_id_for_agent(agent_id) → vm_id (= device_id)
    → get_pc_client_manager(user_id)  ← 无 pc_client_id，取第一个
    → pc_manager.vm_start(vm_id, body)
    → CloudBridge 转发到 Tauri → VmControl 执行

devices/start:
  前端 api.devices.start(deviceId, pcClientId?)
    → Gateway POST /api/devices/{device_id}/start?pc_client_id=xxx
    → _get_pc_manager_for_device(device, user_id, pc_client_id)
    → get_pc_client_manager(user_id, pc_client_id or device.pc_client_id)
    → mgr.vm_start(vm_id=device.id, body)
    → CloudBridge 转发到 Tauri → VmControl 执行
```

### 3.4 差异总结

| 项目 | vm/start | devices/start |
|------|----------|---------------|
| 多 PC 支持 | ❌ 无 | ✅ pc_client_id |
| 适用场景 | 旧 Agent 中心流程 | 新 Device 中心流程、多 PC |
| 建议 | 若需多 PC，应增加 pc_client_id 或迁移到 devices |
| 数据来源 | agent_binding → device_id | devices 表直接 |

---

## 四、Internal API 与公开 API 边界

### 4.1 访问控制

| 类型 | 路径 | 访问限制 | 说明 |
|------|------|----------|------|
| **公开 API** | `/api/*`（除 internal） | JWT + nginx auth_request | 前端、Tauri 调用 |
| **Internal** | `/internal/*` | nginx `allow 127.0.0.1; deny all` | 仅本机服务 |
| **Internal 子路径** | `/internal/auth/validate` | 同上 | nginx auth_request 子请求 |
| **Internal 子路径** | `/internal/pc/ws` | JWT + auth_request | CloudBridge WebSocket |

### 4.2 Internal API 清单

| 路径 | 用途 | 调用方 |
|------|------|--------|
| `/internal/auth/validate` | JWT 校验，返回 X-User-ID | nginx auth_request |
| `/internal/pc/ws` | CloudBridge WebSocket | Tauri App |
| `/internal/subagents/*` | SubAgent 生命周期、工具 | Tools Server、RO |
| `/internal/agents/{id}/*` | Agent 内存、notebook、drive、VM 工具 | Tools Server |
| `/internal/messages/*` | 消息、claim、confirm | agent-runtime |
| `/internal/config/*` | LLM 配置等 | agent-runtime |
| `/internal/runtimes/*` | 原 RO 转发（已废弃） | - |

### 4.3 公开 API 与 Internal 边界

| 边界 | 说明 |
|------|------|
| **鉴权** | 公开 API 需 JWT；Internal 仅 127.0.0.1，部分仍需 JWT（如 /internal/pc/ws） |
| **转发** | Gateway 不转发 Internal 到 RO（`_RO_FORWARDED_PREFIXES` 已无匹配） |
| **服务间** | Tools Server、RO、agent-runtime 调用 Gateway Internal |
| **设备连接** | Tauri CloudBridge 连接 `/internal/pc/ws`，Gateway 通过此连接转发 VM 请求 |

### 4.4 特殊端点

| 路径 | 类型 | 说明 |
|------|------|------|
| `GET /api/p2p/validate-device` | 公开 | Relay 服务调用，因 /internal 仅 127.0.0.1，Relay 无法访问 |
| `POST /api/internal/tasks` | 公开（/api 前缀） | 任务 API，内部使用，仍走 /api 路由 |

---

## 五、Gateway vs Tauri 职责边界表

### 5.1 核心职责表

| 职责 | Gateway | Tauri | 备注 |
|------|:-------:|:-----:|------|
| VNC 路由（本机/远端） | | ✅ | vnc_proxy route_vnc |
| VNC WebSocket 代理 | | ✅ | vnc_proxy 监听、QUIC 桥接 |
| Relay 连接建立 | | ✅ | relay::connect_via_relay |
| Relay 会话创建 | ✅ | | relay-request、推 connect_relay |
| Relay 会话校验 | ✅ | | validate-relay-session |
| P2P 心跳接收 | ✅ | | heartbeat |
| P2P locate | ✅ | | 查询目标 PC 地址 |
| my-devices | ✅ | | 供 Tauri 解析 pc_client_id |
| VM 启动编排 | ✅ | | vm/start、devices/start |
| VM 实际执行 | | ✅ | VmControl via CloudBridge |
| CloudBridge 连接 | ✅ | | /internal/pc/ws 接收 |
| CloudBridge 客户端 | | ✅ | 连接 Gateway、转发请求 |
| 多 PC 路由（devices） | ✅ | | pc_client_id |
| 多 PC 路由（vm） | ❌ | | 无 pc_client_id |
| Agent-Device 解析 | ✅ | | _resolve_vm_id_for_agent |

### 5.2 数据流简图

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                      Gateway                             │
                    │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
                    │  │ P2P API     │  │ VM/Devices   │  │ Internal        │  │
                    │  │ heartbeat   │  │ start/stop   │  │ /internal/pc/ws │  │
                    │  │ locate      │  │ status       │  │ auth/validate   │  │
                    │  │ relay-req   │  │              │  │                 │  │
                    │  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘  │
                    │         │                │                    │          │
                    └─────────┼────────────────┼────────────────────┼──────────┘
                              │                │                    │
                    heartbeat │                │ proxy_request       │ WS
                    locate    │                │ (vm_start etc)      │
                              ▼                ▼                    ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                      Tauri App                            │
                    │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
                    │  │ P2P Client  │  │ CloudBridge  │  │ VncProxy        │  │
                    │  │ relay conn  │  │ 转发到       │  │ route_vnc       │  │
                    │  │             │  │ VmControl    │  │ 本机/远端        │  │
                    │  └─────────────┘  └──────────────┘  └─────────────────┘  │
                    └─────────────────────────────────────────────────────────┘
```

### 5.3 建议与待办

| 项目 | 建议 |
|------|------|
| vm/start 多 PC | 增加 `pc_client_id` 参数或引导使用 devices/start |
| Internal 文档 | 维护 Internal API 清单，明确调用方与鉴权 |
| 职责文档 | 本表可作为架构评审与重构参考 |

---

## 六、参考文件

| 文件 | 说明 |
|------|------|
| `novaic-app/src-tauri/src/vnc_proxy.rs` | VNC 路由、本机/远端决策 |
| `novaic-app/src-tauri/src/commands/vnc_urls.rs` | get_vnc_proxy_url、pc_client_id 解析 |
| `novaic-gateway/gateway/api/vm.py` | vm/start、_resolve_vm_id_for_agent |
| `novaic-gateway/gateway/api/devices.py` | devices/start、_get_pc_manager_for_device |
| `novaic-gateway/gateway/api/p2p.py` | heartbeat、locate、relay-request |
| `novaic-gateway/gateway/api/internal/pc_client.py` | DeviceRegistry、get_pc_client_manager |
| `novaic-app/src-tauri/p2p/src/relay.rs` | connect_via_relay |
| `docs/RESEARCH-gateway-forward-to-ro.md` | Internal 转发分析 |
