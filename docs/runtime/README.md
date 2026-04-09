# Agent Runtime 拆页地图
> 路径：`docs/runtime/`

专门针对任务消费端、防风暴唤醒设计以及 AI “React” 思维环的底层剥析。与 [docs/runtime-architecture.md](../runtime-architecture.md) 配合食用。

## 目录索引

| 专题 | 说明 |
|------|------|
| [watchdog-and-dedup.md](watchdog-and-dedup.md) | **Watchdog 巡航犬**：它是怎么无感跨界读表，又怎么在多台 Worker 服务器同时看到这个“大肥肉”时，巧妙通过 Queue 去重并建立防风暴系统 (`SYSTEM_WAKE` 问题)。 |
| [saga-state-machine.md](saga-state-machine.md) | **Saga 无尽长程流水线**：解释 `Task` 跟 `Saga` 的终极区别。以及 `MessageProcess` 与 `SubAgent` 两个最长线工作流是怎么写死在 Python 里的。 |
| [react-agent-loop.md](react-agent-loop.md) | **React 思考循环 (Agent Loop)**：真正的 AI 干活地带。深入 `llm_handlers`、拆解我们怎么在 Prompt 里要求输出 `<think>` 然后发往 Factory。 |
| [tool-chain-dispatch.md](tool-chain-dispatch.md) | **动作分发代理 (Action Dispatch)**：当初那个肥大的 Tools Server 被干掉以后，怎么有的发向云网关打 WebRTC、有的发向 Cortex 写知识图谱了？ |
