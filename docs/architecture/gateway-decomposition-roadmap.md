# Gateway 分解与服务拓扑演进路线图

> **历史路线图归档**：本文记录 Gateway 分解过程中的阶段性判断，不作为当前
> 服务拓扑契约。当前拓扑以 `docs/architecture/service-topology.md`、
> `docs/architecture/overview.md` 和源码启动脚本为准。

本文档记录了从单体 Gateway 向多模块独立微服务演进的架构决策、历史包袱清理进度以及未来工作指南。

## 1. 核心困境：单体 Gateway 的职责失控

在最初的设计中，`novaic-gateway` 被赋予了所有同步入口的调度权，但随着系统膨胀，它开始悄悄背负了太多本质上不属于网关的职责：

1. **客户端 WebSocket 的直接宿主**：处理 App 的连接和极高频的心跳。
2. **Runtime Context 组装与发起**：包办 `SubAgent` 的孵化、进度追踪。
3. **带状态的工具执行容器**：充当所有 Tool (包含 Terminal, Qemu, VM) 的 HTTP 透传中枢。
4. **数据库单点**：死死握着 `gateway.db`，所有服务都需要跨进程查网关的 DB。

随之产生的幻觉是：开发过程中引入了一个所谓的 **"Runtime Orchestrator (RO)"** 概念，试图将执行逻辑剥离，产生了一堆 `RuntimeOrchestratorClient` 和死端点。然而实际上，**RO 服务从未以独立服务的形式真实存在过**，真正的 Runtime 长时任务一直是由 RabbitMQ (Saga Worker / Task Worker / Watchdog) 承担。

## 2. 破局：架构重定义的唯一真理

基于对源码的深层盘点，我们确定了当前真实的物理与逻辑拓扑界限：

| 模块类别 | 职责范围与演进结论 |
|---------|------------------|
| **Gateway (网关)** | **纯粹的无状态防线与同步路由**。接收来自 Entangled (客户端) / 外部 HTTP，做鉴权后，立即投入 Queue Service。从此切断它对 SubAgent 生命周期逻辑的执念。 |
| **Worker Trio (打工三人组)** | Saga Worker / Task Worker / Watchdog 构成了真正的异步长时引擎（所谓 RO 的平替）。负责处理长时间生成的 LLM 队列。 |
| **Cortex (代理大脑)** | **12大工具代理中介与上下文存储**。代理工具调用、隔离执行沙箱，维护基于 `dfs` (Context Engine) 的对话层栈级文件记录 (`/ro/` 与 `/rw/`)。 |
| **Entangled (统一数据桥)** | 提供真正的强一致状态管理，取代所有的长连接拉锯战，统一接管 Client 的 UI Sync（完全架空 Gateway websocket 层）。 |

## 3. 已完成里程碑 (2026-04)

### 3.1 肃清虚假的 "Runtime Orchestrator"
- ✅ **彻底删除 RO 客户端**：清空了 `RuntimeOrchestratorClient` 所有死代码。
- ✅ **切断 Gateway 与 RO 的耦合**：移除了 `subagent.spawn`、`cancel` 等尝试呼叫 RO 的无效操作。
- ✅ **净化配置链路**：从 `services.json`, `config.py`, `strict_config.py` 和 `main_novaic.py` 的启动参中全域清除了近 20 个 RO 废弃参数。

### 3.2 归位 Cortex 的统配权
- ✅ **全局配置标准化**：废除了靠 `os.environ.get("NOVAIC_CORTEX_URL")` 裸调的硬编码恶习，正式并入 `services.cortex` json 结构与 `strict_config` 的强校验保护体系。要求所有 `Task Worker` 及 `Watchdog` 提供确定的 Cortex 注入参数。

## 4. 下一步拆解任务 (TODO)

Gateway 虽然移除了 RO，但仍然存在以下严重的技术债和过度耦合，需在此路线上继续拔除：

### 4.1. 工具服务分离边界
Gateway 目前的 `/internal/tools/...` 接口包揽了 Agent 容器、Shell 命令的下发。实质上，Cortex 才应该直飞 VMControl，当前必须通过 Gateway 转发是一层无意义的 Proxy。
* **行动**：工具执行由 Agent Runtime 内置 dispatcher 接管；Cortex / Runtime 按真实工具边界直连所需服务，砍掉 Gateway 中无状态工具透传端点。

### 4.2. 云端强耦合剥离 (CloudBridge / `pc_client.py`)
Gateway 的 WS 层仍咬死绑定了云端桌面投影等双向通信，必须剥离到单独的连接层去释放。

### 4.3. 解除对 SQLite 的跨进程热诉求
Gateway 目前仍持有大量核心逻辑（Agent 创建，Chat 流控），需要将对外的长时状态管理全权转让给 Entangled 实体库，自身成为全透明网关。
