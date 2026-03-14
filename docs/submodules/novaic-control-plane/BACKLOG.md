# Development Backlog

开发待办，按优先级排序。完成后移至对应 round 或关闭。

---

## 待办

### 1. 抽取 task_queue 公共代码

- **描述**：agent-runtime、tools-server、runtime-orchestrator 三个 repo 中的 `task_queue/client.py`、`utils/`、`business/` 等重复，抽到 novaic-shared-runtime-common 或新建 novaic-shared-task-queue
- **涉及**：novaic-agent-runtime, novaic-tools-server, novaic-runtime-orchestrator
- **优先级**：P2（维护成本变高时再处理）

### 2. 修复工具执行时间长后失败的问题

- **描述**：工具执行时间过长后会失败（可能超时、心跳、连接断开等）
- **根因**：saga.parallel 等待子任务完成时使用 TASK_TIMEOUT(60s)，而 tool.execute 可能需更久；心跳正常，非心跳问题
- **修复**：saga.parallel 等待超时改为 SAGA_STEP_TIMEOUT(1500s)，task 有心跳续约即可长时间执行
- **涉及**：novaic-agent-runtime task_queue/workers/task_worker_sync.py
- **优先级**：P1

### 3b. 工具执行失败时组装 LLM context 的工具结果问题

- **描述**：工具执行失败时，组装 LLM context 阶段对工具结果的处理有问题（失败结果如何展示、截断、或导致后续异常）
- **涉及**：context_builder、LLM 输入组装、tool result 格式化
- **优先级**：P1

### 4. 默认 rest / 默认 reply 的设计与实现

- **描述**：需要思考并解决「默认 rest」「默认 reply」的行为设计（何时触发、如何配置、与 subagent wake 的交互等）
- **涉及**：待设计（可能 gateway subagent、runtime_rest、wake_triggers、前端交互）
- **优先级**：P1

### 5. context 组装与 user message 的问题

- **描述**：context 组装时 user message 的处理存在问题（待细化具体现象）
- **涉及**：待定位（可能 context_builder、LLM 输入、消息格式）
- **优先级**：P1

### 6. 简化 VMUSE 通信：通过 shell exe curl 执行多数工具

- **描述**：简化 VMUSE 与 VM 内工具的通信方式，尽量用「shell 执行 exe + curl」替代当前复杂协议，减少 VMUSE 通信层复杂度
- **涉及**：novaic-mcp-vmuse、tools_server executor、VM 内工具部署方式
- **优先级**：P2

### 7. 优化 app 的 execution log 多agent

- **描述**：优化桌面端 execution log 的展示、性能或交互体验
- **涉及**：novaic-app 前端、execution log 组件、SSE 事件处理
- **优先级**：P2

### 8. 优化输入框

- **描述**：优化聊天输入框的交互、体验或功能
- **涉及**：novaic-app 前端、输入框组件
- **优先级**：P2

### 9. 云端运行 + 登录 + app 架构思考

- **描述**：思考并设计云端运行能力（runtime 部署在云端）、用户登录/鉴权、以及 app 如何对接（本地 app 连接云端 vs 纯 Web）。agent-runtime、gateway、tools-server、RO 等均可部署云端，app 仅保留 UI + 连接层
- **涉及**：架构设计、gateway 鉴权、多租户、novaic-app 改造
- **优先级**：P2（战略方向）

---

## 已关闭

### 修复 runtime 过长时立即启动新 runtime 丢失 context 问题 (2026-03)

- **修复**：将 add_to_hrl 从 Summarize（异步）移至 RuntimeComplete（同步）
- **涉及**：agent-runtime, tools-server, runtime-orchestrator 的 task_queue/sagas
