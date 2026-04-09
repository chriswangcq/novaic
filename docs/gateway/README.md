# Gateway 网关架构拆页地图

> 本目录（`docs/gateway/`）提供 `novaic-gateway` 云端服务网关架构的最细粒度源码级拆解。了解作为系统的门面和调度核心的网关是如何协同各类组件全流程工作的。

与主干架构文档 [docs/gateway-architecture.md](../gateway-architecture.md) 配合食用。

## 目录索引

### 网络与连接生命线
| 专题 | 说明 |
|------|------|
| [rest-auth-and-deps.md](rest-auth-and-deps.md) | FastAPI 路由配置栈，双轨鉴权（Token VS. Nginx Header），以及全局权限依赖链 `get_current_user`。 |
| [cloudbridge-vm.md](cloudbridge-vm.md) | `CloudBridge WS`：云网关是如何穿透回连开发者或客户端本机上的 `VmControl` 去管理 VM 资源的。 |
| [app-ws-and-signaling.md](app-ws-and-signaling.md) | `AppBridge WS`：不仅提供数据推送，且承载了 WebRTC Offer/Answer/ICE 打洞信令的共轨传输。 |

### 数据库层融合记录
| 专题 | 说明 |
|------|------|
| [entangled-hooks.md](entangled-hooks.md) | 业务侵入点剖析：网关继承自 `Entangled` 且用各种 `before/after` Hook 发送附带行为。 |
| [db-v63-split.md](db-v63-split.md) | “表消融时代”：v63 版本的 Scheme DROP 操作记录，哪些走了 Entangled（业务表），哪些留在了基础层（运维/全局配置）。 |

### 内部微服务微循环
| 专题 | 说明 |
|------|------|
| [internal-and-workers.md](internal-and-workers.md) | 给内部 Worker / Saga 反向调用的 `/internal` 接口组，以及与 Factory / Cortex 是如何互动的（含 Worker SSE 保活或信号机制的残留说明）。 |
