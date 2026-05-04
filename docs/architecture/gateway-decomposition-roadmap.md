# Gateway 分解归档

> **历史路线图归档**：本文只保留 Gateway 从单体服务拆分到薄边缘服务的考古结论。
> 当前运行契约以 [service-topology.md](service-topology.md)、
> [overview.md](overview.md)、[gateway-v2-target-architecture.md](gateway-v2-target-architecture.md)
> 和 [../gateway/README.md](../gateway/README.md) 为准。

## 当前结论

Gateway 已从旧的 "God Module" 收窄为薄边缘：

| Gateway 现在拥有 | Gateway 不再拥有 |
| --- | --- |
| Auth / token / api-key 边界 | Agent wake 编排 |
| App WS push / signaling | Entangled schema authority |
| Entangled sync endpoint discovery | 业务 entity proxy |
| TURN / WebRTC signaling 参数 | Runtime tool registry |
| Blob edge | Cortex scope / context / summary |

App 的业务数据主路径是：

```text
App
  -> Entangled sync/action
  -> Business action hooks
  -> Environment notification
  -> Queue / Runtime
```

Gateway 不再是用户消息、Agent 状态、SubAgent 生命周期或工具执行的业务中心。

## 历史问题

早期 Gateway 同时承担了 HTTP edge、WebSocket、业务实体、Runtime 调度、工具透传和部分设备通信。
这种形态制造了几个错误心智模型：

- 以为 Runtime Orchestrator 是独立真实服务。
- 以为 Gateway 是业务 entity / schema 的权威。
- 以为工具执行需要经过 Gateway 无状态透传。
- 以为 Gateway DB 是 Agent / message 的业务主表。

这些路径已经被后续拆分清理。若旧票、旧 runbook 或历史截图仍出现这些说法，按考古文本处理，不要作为新实现依据。

## 当前阅读入口

- 当前服务拓扑：[service-topology.md](service-topology.md)
- 当前 Gateway 边界：[gateway-v2-target-architecture.md](gateway-v2-target-architecture.md)
- Gateway 专题：[../gateway/README.md](../gateway/README.md)
- App/Entangled 通信：[entangled-store-and-app-ws.md](entangled-store-and-app-ws.md)
- Agent 管线：[agent-pipeline.md](agent-pipeline.md)

## 防回归原则

- 不新增 Gateway 业务 entity proxy。
- 不新增 Gateway tool registry。
- 不让 Gateway 参与 Agent wake / Queue session / Cortex scope。
- 不通过 Gateway REST 发用户聊天消息；聊天动作走 Entangled action + Business hook。
- 不把 Gateway 本地 DB 当业务状态源。
