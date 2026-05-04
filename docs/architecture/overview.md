# NovAIC 架构概览（L1）

本文档描述父仓库视角的当前系统拓扑。细节以各子模块源码和专题文档为准；历史 Gateway-centric、TRS、Runtime Orchestrator、Gateway entity proxy 叙述不作为当前实现依据。

## 1. 当前逻辑拓扑

```text
App
 ├─ HTTP/WS → Gateway：Auth、Blob Proxy、App push/signaling、Entangled endpoint discovery
 ├─ WS      → Entangled：实体同步、本地 Rust SQLite cache
 └─ action  → Entangled → Business：messages.send / devices / agents / skills 等产品动作

Business
 ├─ HTTP → Entangled：服务端 entity/action 写入方
 ├─ HTTP → Device：设备/VM/WebRTC/hardware 编排
 ├─ Environment → Subscriber → Queue：Agent wake 触发
 └─ internal API：Runtime tool/product 配置入口

Runtime
 ├─ Queue Service：Task/Saga/session 调度
 ├─ Workers → Cortex：scope/context/reasoning/action/observation
 ├─ Workers → LLM Factory：模型调用
 └─ Workers → Business/Device/Cortex/native executor：工具执行

Cortex
 └─ Agent 工作轨迹与上下文：agent-root scope tree、payload refs、summary.md

Device
 └─ CloudBridge/VmControl/WebRTC/VM/HD 硬件执行
```

## 2. 服务职责

| 服务 | 职责 |
|---|---|
| `novaic-app` | React/Tauri UI、本地 Entangled Rust cache、本地 VmControl |
| `novaic-gateway` | 薄边缘：Auth、App WS、TURN、Blob Proxy、Entangled sync endpoint discovery |
| `Entangled` | 实体存储、schema/action 注册、HTTP + sync WS |
| `novaic-business` | 产品业务：action hooks、Environment、SubAgent、Device 编排、配置/API |
| `novaic-agent-runtime` | Queue Service、Saga/Task Workers、Health、Scheduler、tool executor |
| `novaic-cortex` | scope tree、LLM context、work trace、payload、sandbox |
| `novaic-device` | Device registry、CloudBridge、hardware/VM/WebRTC API |
| `novaic-storage-a` | Blob Service：字节与大对象 |
| `novaic-llm-factory` | provider/API key/model routing，标准 chat completions |
| `novaic-quic-service` | STUN/Relay/静态资源 CDN 等网络边缘能力 |

## 3. 端口约定

**Backend（云端/服务端）**

| 服务 | 端口 | 说明 |
|---|---:|---|
| `entangled` | 19900 | 实体同步引擎 |
| `gateway` | 19999 | Auth/App WS/Blob Proxy/TURN |
| `business` | 19998 | 产品业务与 action hooks |
| `device` | 19993 | 设备与硬件执行 |
| `queue_service` | 19997 | Task/Saga/session 调度 |
| `cortex` | 19996 | Agent 工作轨迹与上下文 |
| `blob_service` | 19995 | Blob Service |

**Client（用户本地）**

| 服务 | 端口 | 说明 |
|---|---:|---|
| `vmcontrol` | 19996 | Tauri 内嵌本地 VmControl；与云端 Cortex 同端口但不同网络侧 |

## 4. 模块速查

| 目录 | 角色 |
|---|---|
| `novaic-app` | 客户端 UI + Tauri + VmControl |
| `novaic-gateway` | 薄边缘 Gateway |
| `novaic-business` | 产品业务服务 |
| `novaic-agent-runtime` | Agent 执行层 |
| `novaic-cortex` | Agent 工作轨迹与上下文 |
| `novaic-device` | 设备/硬件服务 |
| `novaic-storage-a` | Blob Service |
| `Entangled` | 实体同步引擎 |
| `novaic-common` | 共享配置、schema、工具合同 |

## 5. 文档地图

| 主题 | 文档 |
|------|------|
| 服务拓扑 | [service-topology.md](service-topology.md) |
| App UI | [app-ui.md](app-ui.md) |
| Agent 管线 | [agent-pipeline.md](agent-pipeline.md) |
| Cortex | [cortex.md](cortex.md), [../cortex/README.md](../cortex/README.md) |
| Gateway | [../gateway-architecture.md](../gateway-architecture.md), [../gateway/README.md](../gateway/README.md) |
| Entangled | [../entangled-architecture.md](../entangled-architecture.md), [../entangled/README.md](../entangled/README.md) |
| 文件与语音 | [../reference/file-service.md](../reference/file-service.md) |
| 配置与环境 | [../reference/config-and-environment.md](../reference/config-and-environment.md) |
