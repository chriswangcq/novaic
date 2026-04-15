# Agent Runtime 运行时架构总览

`novaic-agent-runtime` 是 NovAIC 大脑的核心引擎。如果说 Gateway 是身体的感受器和网柄，Cortex 是记忆海马体，那么 Runtime 就是真正的“前额叶思考皮层与控制干”。

---

## 1. 独立而剥离的生命结构
Runtime 是一组可以在任意无头服务器成百上千个拉起的**无状态 Python 进程集合**。它本身没有自己的强状态 SQL 数据库。它仅拥有 `Queue Service` (任务队列 DB)。
所有的输入端来自 Gateway 写入的 Entangled `_chat_messages` 表，输出则写向 Cortex (认知记忆) 或是向下反开给 Gateway 执行。

启动体系 (`main_novaic.py`) 里，它通过不同的命令分裂成不同人格的守卫：
- **`queue-service`**: 监听 19997。内存级别的任务分发器，依托一套自带的 sqlite 作为底舱记录排队工单。
- **`task-worker`**: 执行短平快 CPU/IO 任务的干活小弟。
- **`saga-worker`**: 长程剧本杀玩家，一步一步推动着 AI 是该思考、还是该回复的流水线机读引擎。
- **`health`**: 超时回收与恢复兜底。
- **`scheduler`**: 唯一的定时唤醒轮询者，扫描 `wake_at` 已过期的 sleeping subagent 并经 Queue Session Coordinator 分发。

## 2. 处理循环：从文字到回复的闭环

```text
 1. 用户点下发送 ──► Gateway.store / Queue dispatch (写入消息并触发运行时)
      │
 2. Queue Session Coordinator 路由 ──► 创建/缓冲 subagent_wake Saga
      │
 3. Saga Worker 认领 ──► 启动「MessageProcess Saga」状态机
      ├─ 节点1: Cortex准备 (组装前序树，拿到 Context)
      ├─ 节点2: React 思考循环 (把上下文发给 llm-factory 并解析结果)
      │      └─ 如果 LLM 返回 Tool Call ──► Saga 下发 ToolTask ──► Task Worker 真正干活再返回
      └─ 节点3: 收尾与答复 ──► 拿着最终答案发起 /internal 找 Gateway，说这消息完事了，改成 "sent"
```

这套长程异步管线使得 NovAIC 从来不怕大规模长时间的思考与复杂操作挂机。随时被杀、随时重启、随时从上一个 Saga 的节点进度接着往下推。详细源码级解析请见内部目录 `docs/runtime/` 专题。
